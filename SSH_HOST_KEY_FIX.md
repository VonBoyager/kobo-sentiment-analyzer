# SSH Host Key Verification Fix

## Problem
Your Digital Ocean droplet's host key has changed, causing SSH to reject the connection for security reasons.

## Why This Happens
- Droplet was recreated/rebuilt
- Server was reinstalled
- Digital Ocean rotated keys (rare)
- **OR** potential security issue (less likely if you just rebuilt)

## Solution: Update Known Hosts

### Option 1: Remove Old Key and Add New One (Recommended)

**On Windows (PowerShell or Command Prompt):**

```powershell
# Remove the old key for this IP
ssh-keygen -R 152.42.220.146

# Or manually edit the file
notepad F:\Users\reflu\.ssh\known_hosts
# Delete line 1 (the offending key)
```

Then connect again - SSH will prompt you to accept the new key:
```powershell
ssh root@152.42.220.146
# Type "yes" when prompted to accept the new key
```

### Option 2: Verify Key First (More Secure)

1. **Get the key fingerprint from Digital Ocean:**
   - Log into Digital Ocean dashboard
   - Go to your droplet
   - Check the console or metadata for the host key fingerprint

2. **Compare with the error message:**
   - Error shows: `SHA256:0qeuwlRObk0Njmi/4YivGbFm9GfCMi6A1T5zylecKEM`
   - If it matches Digital Ocean's, it's safe

3. **Remove old key and connect:**
   ```powershell
   ssh-keygen -R 152.42.220.146
   ssh root@152.42.220.146
   ```

### Option 3: Temporarily Disable Strict Checking (NOT Recommended for Production)

```powershell
# Only use this if you're certain it's safe
ssh -o StrictHostKeyChecking=no root@152.42.220.146
```

## Quick Fix Commands

**Windows PowerShell:**
```powershell
# Remove old key
ssh-keygen -R 152.42.220.146

# Connect (will prompt to accept new key)
ssh root@152.42.220.146
```

**Or manually edit known_hosts:**
```powershell
# Open known_hosts file
notepad $env:USERPROFILE\.ssh\known_hosts

# Delete the line containing 152.42.220.146 (line 1 according to error)
# Save and close

# Connect again
ssh root@152.42.220.146
```

## Verify the New Key

After connecting, verify the fingerprint matches:
```bash
# On the server, check the host key fingerprint
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Should show: `SHA256:0qeuwlRObk0Njmi/4YivGbFm9GfCMi6A1T5zylecKEM`

## Prevention

### For Future Rebuilds

1. **Save your server's host key fingerprint** when first setting up:
   ```bash
   ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
   ```

2. **Store it securely** for reference

3. **Use SSH config file** to manage keys:
   ```powershell
   # Create/edit SSH config
   notepad $env:USERPROFILE\.ssh\config
   
   # Add:
   Host droplet
       HostName 152.42.220.146
       User root
       StrictHostKeyChecking yes
       UserKnownHostsFile ~/.ssh/known_hosts
   ```

## Security Note

If you **didn't** rebuild the droplet and this error appears:
1. **DO NOT** connect immediately
2. Check Digital Ocean dashboard - was the droplet recreated?
3. Verify the fingerprint through Digital Ocean console
4. If unsure, contact Digital Ocean support

## After Fixing

Once connected, you can continue with your deployment:
```bash
cd ~/kobo-sentiment-analyzer-master
git pull
docker-compose down
docker-compose up -d
```

