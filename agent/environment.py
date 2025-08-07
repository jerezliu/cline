import os
import platform
import subprocess

class EnvironmentManager:
    """Gathers information about the execution environment."""

    def get_cwd(self) -> str:
        """Returns the current working directory."""
        return os.getcwd()

    def get_os(self) -> str:
        """Returns the operating system."""
        return platform.system()

    def get_shell(self) -> str:
        """Returns the default shell."""
        return os.environ.get("SHELL", "Unknown")

    def get_file_listing(self, cwd: str) -> str:
        """Returns a string listing files in the current directory, excluding .git."""
        try:
            # Using 'ls -lA' for a detailed, long format listing including hidden files
            result = subprocess.run(
                ["ls", "-lA", cwd],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            return f"Could not list files: {e}"

    def get_git_remotes(self, cwd: str) -> str:
        """Returns a string of git remote URLs."""
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "Not a git repository or git is not installed."

    def get_context(self) -> dict:
        """Returns a dictionary of the environment context."""
        cwd = self.get_cwd()
        return {
            "cwd": cwd,
            "os": self.get_os(),
            "shell": self.get_shell(),
            "file_listing": self.get_file_listing(cwd),
            "git_remotes": self.get_git_remotes(cwd),
        }

    def get_environment_details(self, mode: str) -> str:
        """Constructs the environment details block."""
        context = self.get_context()
        details = f"""<environment_details>
# System Information
Operating System: {context['os']}
Default Shell: {context['shell']}
Current Working Directory: {context['cwd']}

# Git Remote URLs
{context['git_remotes']}

# Files
{context['file_listing']}
# Current Mode
{mode.upper()} MODE
</environment_details>"""
        return details
