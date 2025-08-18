# Secure Git Setup on a Shared PC (Per-User Accounts)
Configure Git and SSH securely when multiple people use the same machine. If you have your own Linux, macOS, or Windows account on the server or PC:

## 1) Configure Git per your user (not system-wide)
```bash
git config --global user.name  "Your Name"
git config --global user.email "you@domain.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```
## 2) Use SSH keys (don’t use HTTPS + stored tokens on shared hosts)
``` bash
ssh-keygen -t ed25519 -C "you@domain.com"
mkdir -p ~/.ssh && chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.pub
# optional: keep agent alive in your session
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```
Add ~/.ssh/id_ed25519.pub to your Git host (GitHub → Settings → SSH and GPG keys).

## 3) (Recommended) Lock the key to your host alias so Git always uses the right key:
``` bash
~/.ssh/config
Host github-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```
Then clone with the alias:
``` bash
git clone github-personal:USER/REPO.git
```
## 4) Work in your home dir (not a shared folder)
``` bash
cd ~/code
git clone github-personal:USER/REPO.git
```
## 5) (Optional, stronger proof it’s you) Sign commits with SSH:
```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```
Enable SSH commit verification on your Git host.
