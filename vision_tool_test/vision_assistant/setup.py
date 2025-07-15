from setuptools import setup, find_packages

# List of dependencies
required = [
    # Core application dependencies
    "opencv-python>=4.9.0",
    "numpy>=1.23.2",
    "Pillow>=11.0.0",
    "PyAutoGUI>=0.9.54",
    "pyperclip>=1.9.0",
    "keyboard>=0.13.5",
    "websockets>=13.1",
    "jsonschema>=4.21.0",

    # # Dependencies for configuration generator
    # "langchain>=0.1.0",
    # "langchain-openai>=0.0.3",
    # "openai-whisper",
    # "soundfile",

    # Development and testing dependencies
    "python-dotenv>=1.0.1",
    "pytest"
]

setup(
    name="vision_assistant_tool",
    version="0.1.2",
    packages=find_packages(where="src"),  # This will find all packages under src/
    package_dir={
        "": "src",  # This tells setuptools that packages are under src/
    },
    install_requires=required,
    author="Bridgent.ai",
    description="A project with Vision Assistant",
    python_requires=">=3.10"
)
