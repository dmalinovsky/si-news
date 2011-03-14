from setuptools import setup

setup(
    name='si-news',
    version='0.1.1',
    description='Tracks updates for zhurnal.lib.ru authors',
    author='Denis Malinovsky',
    author_email='dmalinovsky@gmail.com',
    url='https://bitbucket.org/dmalinovsky/si-news/',
    py_modules=['si_news'],
    install_requires=['distribute', 'pyquery'],
    license='gpl',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: Russian',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities',
        ],
    entry_points = {
        'gui_scripts': [
            'si_news = si_news',
            ]
        },
)
