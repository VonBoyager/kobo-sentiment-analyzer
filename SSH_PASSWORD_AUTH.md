# Fix SSH Permission Denied (publickey)

## Problem
SSH is trying to use key authentication, but you don't have a key set up or it's not authorized.

## Solutions

### Option 1: Use Password Authentication (Quickest)

If password authentication is enabled on your droplet:

```powershell
# Force password authentication
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@152.42.220.146
```

Or:

```powershell
ssh -o PasswordAuthentication=yes root@152.42.220.146
```

### Option 2: Check if Password Auth is Enabled

First, you need to access the droplet via Digital Ocean console to check/enable password auth:

1. Go to Digital Ocean dashboard
2. Click on your droplet
3. Click "Access" → "Launch Droplet Console"
4. Log in with root password

Then on the droplet, check SSH config:

```bash
# Check if password authentication is enabled
sudo grep -i "PasswordAuthentication" /etc/ssh/sshd_config

# If it shows "PasswordAuthentication no", enable it:
sudo nano /etc/ssh/sshd_config
# Change: PasswordAuthentication no → PasswordAuthentication yes
# Save and exit (Ctrl+O, Enter, Ctrl+X)

# Restart SSH service
sudo systemctl restart sshd
```

### Option 3: Set Up SSH Key Authentication (Recommended)

#### Step 1: Generate SSH Key on Windows (if you don't have one)

```powershell
# Generate new SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Press Enter to accept default location (C:\Users\reflu\.ssh\id_ed25519)
# Enter a passphrase (optional but recommended)
```

#### Step 2: Copy Public Key to Droplet

**Method A: Using ssh-copy-id (if available)**
```powershell
# Install OpenSSH client tools if needed
# Then:
ssh-copy-id root@152.42.220.146
```

**Method B: Manual Copy (Windows)**

```powershell
# View your public key
cat $env:USERPROFILE\.ssh\id_ed25519.pub

# Copy the output, then on the droplet console:
# Run: mkdir -p ~/.ssh && echo "your-public-key-here" >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

**Method C: Using PowerShell to Copy**

```powershell
# Get your public key
$pubkey = Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub

# Connect and add key (will prompt for password once)
ssh root@152.42.220.146 "mkdir -p ~/.ssh && echo '$pubkey' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

### Option 4: Use Digital Ocean Console (Easiest for First Time)

1. **Access via Digital Ocean Console:**
   - Go to Digital Ocean dashboard
   - Click your droplet
   - Click "Access" → "Launch Droplet Console"
   - Log in with root password

2. **Once in the console, enable password auth (if needed):**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Find and change: PasswordAuthentication yes
   sudo systemctl restart sshd
   ```

3. **Or add your SSH key:**
   ```bash
   # Create .ssh directory
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   
   # Add your public key (paste it)
   nano ~/.ssh/authorized_keys
   # Paste your public key, save (Ctrl+O, Enter, Ctrl+X)
   
   # Set correct permissions
   chmod 600 ~/.ssh/authorized_keys
   ```

## Quick Fix Commands

### Try Password Auth First:
```powershell
ssh -o PreferredAuthentications=password root@152.42.220.146
```

### If That Doesn't Work:
1. Use Digital Ocean console to access droplet
2. Enable password auth or add your SSH key
3. Then connect normally

## Verify Your Setup

After setting up, test connection:

```powershell
# Test with verbose output to see what's happening
ssh -v root@152.42.220.146
```

This will show you exactly what authentication methods are being tried.

