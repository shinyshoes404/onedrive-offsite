from setuptools import setup

with open("README.md", "r") as fh:
    readme_long_description = fh.read()

setup(
    name='onedrive-offsite',
    version='1.0.1', 
    description="Application to automatically encrypt backup files (ex: vma.zst from Proxmox) and push them to Microsoft OneDrive.",
    long_description=readme_long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/shinyshoes404/onedrive-offsite',
    author='shinyshoes',
    author_email='shinyshoes404@protonmail.com',
    license='MIT License',
    packages=['onedrive_offsite'],
    package_dir={'':'src'},
    entry_points = { 'console_scripts' : ['onedrive-offsite-signin=onedrive_offsite.app_setup:signin',
                                        'onedrive-offsite-setup-app=onedrive_offsite.app_setup:app_info_setup',
                                        'onedrive-offsite-create-key=onedrive_offsite.app_setup:create_key',
                                        'onedrive-offsite-upload-backup-file=onedrive_offsite.file_ops:crypt_file_upload',
                                        'onedrive-offsite-build-and-upload=onedrive_offsite.file_ops:crypt_file_build_and_upload',
                                        'onedrive-offsite-build-crypt-file=onedrive_offsite.file_ops:crypt_file_build',
                                        'onedrive-offsite-restore=onedrive_offsite.file_ops:restore',
                                        'onedrive-offsite-download=onedrive_offsite.file_ops:download']},
    
    install_requires=[
        'cryptography', 'requests', 'flask', 'py-basic-ses', 'mock'   
    ],

    extras_require={
        # To install requirements for dev work use 'pip install -e .[dev]'
        'dev': ['coverage']
    },

    python_requires = '>=3.7.*',

    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: POSIX :: Linux',           
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
)
