### This supplement waiting on upstream improvements to and might be updated and released when they're ready

#%% [markdown]
"""
## Universal Pathlib

The last thing I want to show today is `universal_pathlib`, found [here](https://github.com/fsspec/universal_pathlib). 
This is a package from `fsspec` that mimics the `pathlib` API.
With this, every filesystem becomes extremely simple to traverse, scan and IO from.

The next example shows the backup example again, but this time using `unversal_pathlib`s `UPath` class. See the [README](https://github.com/fsspec/universal_pathlib) for more details on how it relates to `pathlib`

Take note: there [are](https://pypi.org/project/upathlib/) [various](https://pypi.org/project/upath/) [other](https://pypi.org/project/universal-pathlib-edge/) `UPath` implementations found in pypi, be careful when trying to install this package from memory!
"""
#%%
!pip install --disable-pip-version-check --root-user-action=ignore -q \
    universal_pathlib

from upath import UPath
source = UPath('source://mybucket/example_file')
target = UPath('target://mybucket/backup_file_2')
target.write_text(source.read_text())

target.read_text()
#%% [markdown]
"""
Most Path functionality works here too, some examples;
"""
#%%
print("globs works...")
print("\t" + str(list(target.parent.glob("**/*"))))
print("stat works...")
print("\t" + str(target.stat()))
#%% [markdown]
"""
If you want to implement a streaming copy between source and target you will have to get a bit creative, below is an example of how it can be done
"""
#%%
stream_target = UPath('target://mybucket/backup_file_3')
with source.open('rb') as source_f, stream_target.open('wb') as target_f:
    while buffer := source_f.read(10):
        target_f.write(buffer)

stream_target.read_text()
#%% [markdown]
"""
Though hopefully by the time you read this, [this issue](https://github.com/fsspec/universal_pathlib/issues/227) is resolved, then it will be possible to use `shutil` to efficiently copy wth UPath.
"""
#%%
import shutil
shutil.copy(source, stream_target)
#%% [markdown]
"""
But not yet..

And that's about all I have to show..hope you learned something useful!
"""
