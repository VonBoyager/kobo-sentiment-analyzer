# SSH Troubleshooting - Password Auth Enabled But Still Denied

## If PasswordAuthentication is Already "yes"

Check these settings in `/etc/ssh/sshd_config`:

### 1. Check PermitRootLogin

```bash
sudo grep -i "PermitRootLogin" /etc/ssh/sshd_config
```

Should be one of:
- `PermitRootLogin yes` (allows password)
- `PermitRootLogin prohibit-password` (only keys)
- `PermitRootLogin without-password` (only keys)

**Fix:**
```bash
sudo nano /etc/ssh/sshd_config
# Change to: PermitRootLogin yes
sudo systemctl restart sshd
```

### 2. Check Authentication Methods

```bash
sudo grep -i "AuthenticationMethods" /etc/ssh/sshd_config
```

If this is set, it might be forcing only publickey.

**Fix:** Comment it out or remove:
```bash
sudo nano /etc/ssh/sshd_config
# Comment out: #AuthenticationMethods publickey
sudo systemctl restart sshd
```

### 3. Check if Root Password is Set

```bash
# Check if root has a password set
sudo passwd -S root
```

If it shows "L" (locked), unlock it:
```bash
sudo passwd root
# Enter new password twice
```

### 4. Check SSH Service Status

```bash
# Check if SSH is running
sudo systemctl status sshd

# Check for errors
sudo journalctl -u sshd -n 50
```

### 5. Verify Config Changes Applied

```bash
# Test SSH config
sudo sshd -t

# Check what SSH is actually using
sudo sshd -T | grep -i password
sudo sshd -T | grep -i permitroot
```

### 6. Try Connecting with Verbose Output

From Windows PowerShell, try:
```powershell
ssh -vvv root@152.42.220.146
```

This will show exactly what authentication methods are being tried and why it's failing.

## Quick Diagnostic Commands

Run these on the droplet (via console):

```bash
# Check all relevant SSH settings
echo "=== SSH Config Check ==="
sudo grep -E "PasswordAuthentication|PermitRootLogin|PubkeyAuthentication|AuthenticationMethods" /etc/ssh/sshd_config

# Check root account status
echo "=== Root Account Status ==="
sudo passwd -S root

# Check SSH service
echo "=== SSH Service Status ==="
sudo systemctl status sshd | head -10

# Test SSH config
echo "=== SSH Config Test ==="
sudo sshd -t
```

## Common Fixes

### Fix 1: Enable Root Login with Password

```bash
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Fix 2: Remove AuthenticationMethods Restriction

```bash
sudo sed -i 's/^AuthenticationMethods/#AuthenticationMethods/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### Fix 3: Set Root Password (if locked)

```bash
sudo passwd root
# Enter password twice
```

## Alternative: Create a New User with Sudo

If root login is restricted, create a new user:

```bash
# Create new user
sudo adduser yourusername

# Add to sudo group
sudo usermod -aG sudo yourusername

# Set password
sudo passwd yourusername
```

Then connect as that user:
```powershell
ssh yourusername@152.42.220.146
```

## Test Connection from Windows

After making changes, test with verbose output:

```powershell
ssh -vvv -o PreferredAuthentications=password root@152.42.220.146
```

The `-vvv` flag shows detailed debug information about what's happening.

