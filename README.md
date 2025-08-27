# Step 1 - Enable the Windows Subsystem for Linux
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

# Step 2 - Check requirements for running WSL 2 (optional)
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

# Step 3 - Download the Linux kernel update package (optional)
[WSL2 Linux kernel update package for x64 machines](https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi)

# Step 4 - Set WSL 2 as your default version (optional)
```powershell
wsl --set-default-version 2
```

# Step 5 - Downloading distributions
```powershell
Invoke-WebRequest -Uri https://aka.ms/wslubuntu2004 -OutFile Ubuntu.appx -UseBasicParsing
```

# Step 6 - Install distro manually
1. Create Ubuntu folder in C:\Users\user\AppData\Local
2. Copy Ubuntu.appx to Ubuntu folder
3. Change appx extention to zip and unzip file
4. Go to unzipped folder and again change Ubuntu_version_x64.appx appx extention to zip and unzip file
5. Go to unzipped folder and run ubuntu.exe and follow the instructions to setup distro
6. In order to run ubuntu you need to install **Terminal** app for windows (follow [this](https://learn.microsoft.com/en-us/windows/terminal/install) link)
