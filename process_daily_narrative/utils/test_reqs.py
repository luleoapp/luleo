import subprocess
import pkg_resources

def get_installed_packages():
    return {pkg.key: pkg.version for pkg in pkg_resources.working_set}

def get_requirements():
    with open('requirements.txt', 'r') as f:
        return {line.split('==')[0].lower(): line.strip() for line in f if line.strip() and not line.startswith('#')}

def main():
    installed = get_installed_packages()
    required = get_requirements()

    missing = []
    for package, version in installed.items():
        if package.lower() not in required:
            missing.append(f"{package}=={version}")

    if missing:
        print("The following packages are installed but not in requirements.txt:")
        for package in sorted(missing):
            print(package)
    else:
        print("All installed packages are in requirements.txt")

    # Check if any package in requirements.txt is not installed
    not_installed = [pkg for pkg in required if pkg.lower() not in installed]
    if not_installed:
        print("\nThe following packages are in requirements.txt but not installed:")
        for package in sorted(not_installed):
            print(package)

if __name__ == "__main__":
    main()