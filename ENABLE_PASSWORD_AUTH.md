# Enable Password Authentication on Droplet

## Current Situation
- Host key is accepted ✅
- But getting "Permission denied (publickey)" ❌
- This means password authentication might be disabled

## Solution: Enable Password Auth via Digital Ocean Console

### Step 1: Access Droplet Console

1. Go to [Digital Ocean Dashboard](https://cloud.digitalocean.com)
2. Click on your droplet (152.42.220.146)
3. Click **"Access"** tab
4. Click **"Launch Droplet Console"**
5. Log in with your root password

### Step 2: Enable Password Authentication

Once in the console, run these commands:

```bash
# Backup SSH config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH config
sudo nano /etc/ssh/sshd_config
```

In the editor, find and change these lines:

```
# Change from:
PasswordAuthentication no
PubkeyAuthentication yes

# To:
PasswordAuthentication yes
PubkeyAuthentication yes
```

**Or** if the lines are commented out (#), uncomment and set:

```
PasswordAuthentication yes
```

Save and exit:
- Press `Ctrl + O` (save)
- Press `Enter` (confirm)
- Press `Ctrl + X` (exit)

### Step 3: Restart SSH Service

```bash
# Test config for errors
sudo sshd -t

# If no errors, restart SSH
sudo systemctl restart sshd
```

### Step 4: Connect from Windows

Now try connecting from PowerShell:

```powershell
ssh root@152.42.220.146
```

Enter your root password when prompted.

## Alternative: Add SSH Key Instead

If you prefer key-based authentication (more secure):

### On Windows (PowerShell):

```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"
# Press Enter for default location
# Enter passphrase (optional)

# View public key
cat $env:USERPROFILE\.ssh\id_ed25519.pub
```

### On Droplet (via Console):

```bash
# Create .ssh directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key (paste the output from Windows)
nano ~/.ssh/authorized_keys
# Paste your public key, save (Ctrl+O, Enter, Ctrl+X)

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys
```

Then connect from Windows:
```powershell
ssh root@152.42.220.146
```

## Quick Commands Summary

**Enable password auth on droplet:**
```bash
sudo sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

**Test connection from Windows:**
```powershell
ssh -v root@152.42.220.146
```

The `-v` flag shows verbose output so you can see what authentication methods are being tried.

## Security Note

- Password authentication is less secure than SSH keys
- Consider setting up SSH keys after initial access
- You can have both enabled (password + keys)

