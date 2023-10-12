from typing import List
import pkg_resources


def list_installed_packages() -> List[str]:
    """
    List all installed Python packages.

    Returns:
        List[str]: A list of installed Python packages.
    """

    # Using pkg_resources to fetch installed packages
    try:
        installed_packages = [d.key for d in pkg_resources.working_set]
        return installed_packages
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    # Fetching and displaying the list of installed packages
    packages = list_installed_packages()
    print("Installed Python Packages:")
    for package in packages:
        print(f"- {package}")
