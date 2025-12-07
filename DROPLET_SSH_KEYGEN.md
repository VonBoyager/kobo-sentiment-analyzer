# SSH Key Management on Digital Ocean Droplet

## Common ssh-keygen Commands on the Droplet

### 1. Check Current Host Key Fingerprint

This is useful to verify the server's host key matches what you see in the error:

```bash
# Check ED25519 host key (most common)
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub

# Check RSA host key
ssh-keygen -lf /etc/ssh/ssh_host_rsa_key.pub

# Check all host keys
for key in /etc/ssh/ssh_host_*_key.pub; do ssh-keygen -lf "$key"; done
```

**Expected output:**
```
256 SHA256:0qeuwlRObk0Njmi/4YivGbFm9GfCMi6A1T5zylecKEM root@your-droplet (ED25519)
```

### 2. Generate New SSH Host Keys (If Needed)

**Warning:** Only do this if you need to regenerate keys. This will require updating known_hosts on all clients.

```bash
# Backup old keys first
sudo cp -r /etc/ssh /etc/ssh.backup

# Remove old host keys
sudo rm /etc/ssh/ssh_host_*

# Generate new host keys
sudo ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""
sudo ssh-keygen -t rsa -b 4096 -f /etc/ssh/ssh_host_rsa_key -N ""

# Restart SSH service
sudo systemctl restart sshd
```

### 3. Generate User SSH Key Pair (For Git, etc.)

If you need to generate a key pair for the root user on the droplet:

```bash
# Generate new key pair
ssh-keygen -t ed25519 -C "droplet-key" -f ~/.ssh/id_ed25519

# Or RSA (if needed)
ssh-keygen -t rsa -b 4096 -C "droplet-key" -f ~/.ssh/id_rsa

# View public key
cat ~/.ssh/id_ed25519.pub
```

### 4. Add Public Key to Authorized Keys

If you want to add a new public key for passwordless login:

```bash
# Add public key to authorized_keys
echo "your-public-key-here" >> ~/.ssh/authorized_keys

# Set correct permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 5. Check SSH Configuration

```bash
# View SSH server config
sudo cat /etc/ssh/sshd_config

# Test SSH config (check for errors)
sudo sshd -t

# View SSH service status
sudo systemctl status sshd
```

### 6. View All SSH Keys on Server

```bash
# Host keys (server identity)
ls -la /etc/ssh/ssh_host_*

# User keys
ls -la ~/.ssh/

# View authorized keys
cat ~/.ssh/authorized_keys
```

## For Your Current Situation

Since you're getting a host key mismatch, you probably just want to **verify the fingerprint**:

```bash
# On your droplet, run:
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

This should show: `SHA256:0qeuwlRObk0Njmi/4YivGbFm9GfCMi6A1T5zylecKEM`

If it matches, the key change is legitimate (droplet was rebuilt).

## Security Best Practices

1. **Don't regenerate host keys** unless absolutely necessary
2. **Backup keys** before making changes
3. **Use ED25519** keys (more secure than RSA)
4. **Disable password authentication** in `/etc/ssh/sshd_config`:
   ```
   PasswordAuthentication no
   PubkeyAuthentication yes
   ```
5. **Restart SSH** after config changes: `sudo systemctl restart sshd`

## Troubleshooting

### If SSH service won't start:
```bash
# Check for errors
sudo journalctl -u sshd -n 50

# Test config
sudo sshd -t

# Restart service
sudo systemctl restart sshd
```

### If you can't connect after key changes:
1. Use Digital Ocean console to access the droplet
2. Check SSH service: `sudo systemctl status sshd`
3. Check firewall: `sudo ufw status`
4. Verify keys exist: `ls -la /etc/ssh/ssh_host_*`

