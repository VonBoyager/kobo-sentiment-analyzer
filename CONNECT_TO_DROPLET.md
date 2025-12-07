# How to Connect to Your Digital Ocean Droplet

## Quick Connection

### From PowerShell or Command Prompt

```powershell
ssh root@152.42.220.146
```

If you set up SSH keys, it will connect automatically. Otherwise, it will prompt for your root password.

### From Git Bash

```bash
ssh root@152.42.220.146
```

## If You Have SSH Key Authentication Set Up

If you've added your public key to the droplet, connection should be automatic:

```powershell
ssh root@152.42.220.146
```

## If You Need Password Authentication

If you're using password authentication:

```powershell
ssh root@152.42.220.146
# Enter your root password when prompted
```

## Using SSH Config File (Recommended)

Create an SSH config file for easier connection:

### On Windows (PowerShell):

```powershell
# Create/edit SSH config
notepad $env:USERPROFILE\.ssh\config
```

Add this content:
```
Host droplet
    HostName 152.42.220.146
    User root
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

Then connect simply with:
```powershell
ssh droplet
```

## First Time Connection Steps

1. **Open PowerShell or Command Prompt**

2. **Connect:**
   ```powershell
   ssh root@152.42.220.146
   ```

3. **Accept the host key** (if prompted):
   ```
   The authenticity of host '152.42.220.146' can't be established.
   Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
   ```

4. **Enter password** (if using password auth):
   ```
   root@152.42.220.146's password: [enter your password]
   ```

5. **You're in!** You should see:
   ```
   root@your-droplet-name:~#
   ```

## Common Connection Issues

### Connection Timeout

If you get "Connection timed out":
- Check firewall settings on Digital Ocean
- Verify the droplet is running
- Check if port 22 is open: `sudo ufw status` (on droplet)

### Permission Denied

If you get "Permission denied":
- Verify you're using the correct password
- Check if SSH key authentication is set up correctly
- Verify user has SSH access

### Connection Refused

If you get "Connection refused":
- SSH service might be down on the droplet
- Check via Digital Ocean console
- Restart SSH: `sudo systemctl restart sshd` (on droplet)

## After Connecting

Once connected, you can:

```bash
# Navigate to your application
cd ~/kobo-sentiment-analyzer-master

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Pull latest changes
git pull

# Restart services
docker-compose restart
```

## Using VS Code Remote SSH (Optional)

If you want to edit files directly in VS Code:

1. Install "Remote - SSH" extension in VS Code
2. Press `F1` → "Remote-SSH: Connect to Host"
3. Enter: `root@152.42.220.146`
4. VS Code will connect and you can edit files directly

## Quick Reference

```powershell
# Basic connection
ssh root@152.42.220.146

# With specific SSH key
ssh -i ~/.ssh/your_key root@152.42.220.146

# With verbose output (for debugging)
ssh -v root@152.42.220.146

# Execute command without entering shell
ssh root@152.42.220.146 "docker-compose ps"
```

## Security Tips

1. **Use SSH keys instead of passwords** (more secure)
2. **Disable root login** and use a regular user with sudo
3. **Change default SSH port** (optional, for security)
4. **Use fail2ban** to prevent brute force attacks

