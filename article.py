#%%
%%capture
%xmode Minimal
import logging, warnings

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)
!docker stop chirpy_donkey nervous_sutherland
!docker rm chirpy_donkey nervous_sutherland
#%% [markdown]
"""
Here is a neat method I found to make accessing blob
storage extremely painless in the Python data eco-system. It's especially nice since the tools
it relies on are extremely widely supported. So if that sounds interesting read on.

The code to for to produce this article can be [found here](https://github.com/Nintorac/fsspec-fun/blob/main/article.py), or if you prefer a `.ipynb` then [check here](https://github.com/Nintorac/fsspec-fun/blob/main/build/article.ipynb)

<details>
<summary>
A quick note on article format (click to expand)
</summary>
---
This article is a little experimental, I want to be able to produce content containing executable Python.
It works OK but is the process is a little convoluted. I think I will end up migrating my site platform to MyST or Sphinx in the future to make it easier.

Check out [github.com/Nintorac/fsspec-fun](https://github.com/Nintorac/fsspec-fun) for the sources.

You should know, when you see a block of Python, the content after it is the output of that bit of code.

eg. printing to console
"""
#%%
print("This code is being executed, and the next box is the output\nit works exactly like it would in a jupyter notebook")
#%% [markdown]
"""
or displaying a variable directly
"""
#%%
123456
#%% [markdown]
"""
---
</details>

## Getting started

First we are going to install a few dependencies.
"""
#%%
!pip install --disable-pip-version-check --root-user-action=ignore -q \
    fsspec pandas
import fsspec, pandas as pd
#%% [markdown]
"""
fsspec which is the star of the article, and Pandas to demonstrate some of the neat interoperability
(but this works with many other libraries eg DuckDB, Polars..[etc](https://filesystem-spec.readthedocs.io/en/latest/#who-uses-fsspec))

fsspec is a neat little tool that aims to provide a unified interface to files wherever they live,
be that locally, in a zip, on http or even FTP! Heres the full list of [built in implementations](https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations)
and a list of [other known implementations](https://filesystem-spec.readthedocs.io/en/latest/api.html#other-known-implementations)

For example;
"""
# %%
fs = fsspec.filesystem('file')
with fs.open('example_file','w') as f:
    f.write('hello')

!cat example_file
#%% [markdown]
"""
Here we create a file named `example_file` in the current working directory, write some text into it and then escape to shell to
print the file using cat.

Here's another example;
"""
#%%
fs = fsspec.filesystem('memory')
with fs.open('example_file','w') as f:
    f.write('a,b,c\n1,2,3')

df = pd.read_csv('memory://example_file')
df
#%% [markdown]
"""
This time we use the 'memory' filesystem, an ephemeral in memory filesystem provided by fsspec
out of the box. We write a csv to it, and then use pandas to read the csv directly.

So pandas supports fsspec out of the box!

## Bucket storage

Ok, lets get a bit more fancy;
"""
#%%
!docker run --name nervous_sutherland --rm -d \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=123456789" \
  quay.io/minio/minio server /data --console-address ":9001"
!sleep 2
!docker exec nervous_sutherland bash -c \
    "mc alias set myminio http://localhost:9000 minio 123456789 && \
    mc mb myminio/mybucket"

!pip install --disable-pip-version-check --root-user-action=ignore -q \
      s3fs
#%% [markdown]
"""
We started a Minio server as a quick and easy alternative to S3, if you are following along
from home and already have access to S3 then you can use that just as easily!

Then we create a bucket in the minio server called `mybucket`.

Finally, we installed `s3fs`, this is an fsspec backend that allows you to access any s3 compatiable.
So lets try the last example again, but writing to s3 now;
"""
#%%
fs = fsspec.filesystem(
    's3',               # this setting tells fsspec to use the s3fs package
    key = 'minio',
    secret = '123456789',
    endpoint_url = 'http://localhost:9000'
)
with fs.open('mybucket/example_file','w') as f:
    f.write('a,b,c\n1,2,3')

df = pd.read_csv('s3://mybucket/example_file')
df
#%% [markdown]
"""
Wait, hang on..permission denied?

Ah! when I use `s3://` protocol with pandas it is not supplying my custom configuration
so its reaching out to the real s3 with my bogus credentials and so...Forbidden!

The solve?
"""
#%%
with fs.open('mybucket/example_file','r') as f:
    df = pd.read_csv(f)
df
#%% [markdown]
"""
Yuck! All those nice ergonomics are gone, a whole extra line of code..let's do better!

## Custom Protocol Defintions

After forgetting about this problem for some time I came across `UPath`, this is another library
from the fsspec project that adds `pathlib.Path` capabilites to fsspec endponts. More on that later...
but in the [README](https://github.com/fsspec/universal_pathlib/blob/3cc0871/README.md) for this library in an out of context example, we find a hint!

Here is the relevant excerpt;
```python3
import fsspec.registry
from fsspec.spec import AbstractFileSystem

class MyProtoFileSystem(AbstractFileSystem):
    protocol = ("myproto",)
    ...  # your custom implementation

fsspec.registry.register_implementation("myproto", MyProtoFileSystem)
```

So let's try something;
"""
#%%
from fsspec import register_implementation
from s3fs import S3FileSystem

class MyProtoFileSystem(S3FileSystem):
    protocol = ('fsspecfun',) # Name of the custom protocol

    def __init__(self, *args, **_):
        super().__init__(
            *args,
            # Configuration we inject into the base protocol
            key = 'minio',
            secret = '123456789',
            endpoint_url = 'http://localhost:9000'
        )

register_implementation("fsspecfun", MyProtoFileSystem) # register the protocol with fsspec

df = pd.read_csv('fsspecfun://mybucket/example_file')
df
#%% [markdown]
"""
Well..it seems to be working but...whats happening here?!

First up we are creating a sub-class of `S3FileSystem`, this is the class that we are fetching when we ran
`fsspec.filesystem('s3')`, convince yourself like this; `type(fsspec.filesystem('s3'))==S3FileSystem`.

This is also the class that implements the fssspec protocol, so our subclass will also implement it!

Then we override this protocol variable..this let's fsspec know when to use this backend implementation.
eg for the `S3FileSytem` this value is `('s3',)`

Next we override the init function, here we ignore any of the fsspec storage options and inject our own.

Once we have the implementation in place, we register it with fsspec, passing in the protocol name again here
-- not sure why it's configured twice, but they both have to match for things to work.

Finally, we read the csv again, but this time we replace the `s3` protocol from the initial attempt with the new one: `fsspecfun`

## Custom Protocol Use cases

Neat, it works! Let's take the idea and glam it up a little;
"""
#%%
def register_custom_fs_protocol(protocol: str, base_protocol: str, storage_options: dict[str, str], *, clobber: bool = False):
    """Register a custom fsspec protocol that applies some storage configuration."""
    overwrite_protocol = protocol

    class MyProtoFileSystem(type(fsspec.filesystem(base_protocol))):
        protocol = (overwrite_protocol,)

        def __init__(self, *args, **_):  # noqa: N804
            super().__init__(*args, **storage_options)

    fsspec.register_implementation(protocol, MyProtoFileSystem, clobber)
#%% [markdown]
"""
In this new version we create the handler class on the fly, you can base it off any fsspec implementation
([full list here](https://filesystem-spec.readthedocs.io/en/latest/api.html#other-known-implementations)) and you can 
give the protocol whatever name you like.

So let's use it to register some custom protocols - to demonstrate this I'll deploy another minio server, and we will backup the example file from the original server to the new one.
"""
#%%
!docker run --name chirpy_donkey --rm -d \
  -p 9002:9000 \
  -p 9003:9001 \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=987654321" \
  quay.io/minio/minio server /data --console-address ":9001"
!sleep 2
!docker exec chirpy_donkey bash -c \
    "mc alias set myminio http://localhost:9000 minio 987654321 && \
    mc mb myminio/mybucket"

#%% [markdown]
"""
<a id="infra"></a>
Here is a quick diagram to try to illustrate the architecture of the infrastructure at this point.
It is rendered a bit more nicely in the repo, [here](https://github.com/Nintorac/fsspec-fun/blob/main/build/article.md#infra)

```mermaid
graph LR
subgraph "Container (nervous_sutherland) #32;"
B[Minio Server 1]
B1["Port 9000 - S3 API  #32;"]
B2["Port 9001 - Console #32;"]
B3[<img height="40px" width="40px" src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMDAgMjAwIj4KICA8IS0tIEJhY2tncm91bmQgY2lyY2xlIC0tPgogIDxjaXJjbGUgY3g9IjEwMCIgY3k9IjEwMCIgcj0iODAiIGZpbGw9IiNDNzIwMzAiLz4KICAKICA8IS0tIEJ1Y2tldCBib2R5IC0gbW9yZSBjdXJ2ZWQgYW5kIGJ1Y2tldC1saWtlIC0tPgogIDxwYXRoIGQ9IgogICAgTTYwIDcwCiAgICBDNjAgNzAsIDEwMCA2MCwgMTQwIDcwCiAgICBMMTMwIDE0MAogICAgQzEzMCAxNDAsIDEwMCAxNTAsIDcwIDE0MAogICAgWgogICIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgCiAgPCEtLSBUb3AgZWxsaXBzZSBmb3IgYnVja2V0IG9wZW5pbmcgLS0+CiAgPGVsbGlwc2UgY3g9IjEwMCIgY3k9IjcwIiByeD0iNDAiIHJ5PSIxMCIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgCiAgPCEtLSBPYmplY3Qgc3RvcmFnZSBzeW1ib2xzIC0gY2VudGVyZWQgYW5kIHdpdGggcGVyc3BlY3RpdmUgLS0+CiAgPHJlY3QgeD0iMTA1IiB5PSI5MCIgd2lkdGg9IjEyIiBoZWlnaHQ9IjEyIiBmaWxsPSIjMzMzMzMzIiB0cmFuc2Zvcm09InNrZXdYKC0xMCkiLz4KICA8cmVjdCB4PSIxMjUiIHk9IjkwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIGZpbGw9IiMzMzMzMzMiIHRyYW5zZm9ybT0ic2tld1goLTEwKSIvPgogIDxyZWN0IHg9IjEwNSIgeT0iMTEwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIGZpbGw9IiMzMzMzMzMiIHRyYW5zZm9ybT0ic2tld1goLTEwKSIvPgogIDxyZWN0IHg9IjEyNSIgeT0iMTEwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIGZpbGw9IiMzMzMzMzMiIHRyYW5zZm9ybT0ic2tld1goLTEwKSIvPgogIAogIDwhLS0gTWluSU8gdGV4dCAtLT4KICA8dGV4dCB4PSIxMDAiIHk9IjE3MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSJ3aGl0ZSI+TWluSU88L3RleHQ+Cjwvc3ZnPg==' /> mybucket]
B --> B2
B --> B3
B --> B1
end
subgraph "Container (chirpy_donkey) #32;"
C[Minio Server 2]
C1["Port 9002 - S3 API #32;"]
C2["Port 9003 - Console #32;"]
C3[<img height="40px" width="40px" src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMDAgMjAwIj4KICA8IS0tIEJhY2tncm91bmQgY2lyY2xlIC0tPgogIDxjaXJjbGUgY3g9IjEwMCIgY3k9IjEwMCIgcj0iODAiIGZpbGw9IiNDNzIwMzAiLz4KICAKICA8IS0tIEJ1Y2tldCBib2R5IC0gbW9yZSBjdXJ2ZWQgYW5kIGJ1Y2tldC1saWtlIC0tPgogIDxwYXRoIGQ9IgogICAgTTYwIDcwCiAgICBDNjAgNzAsIDEwMCA2MCwgMTQwIDcwCiAgICBMMTMwIDE0MAogICAgQzEzMCAxNDAsIDEwMCAxNTAsIDcwIDE0MAogICAgWgogICIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgCiAgPCEtLSBUb3AgZWxsaXBzZSBmb3IgYnVja2V0IG9wZW5pbmcgLS0+CiAgPGVsbGlwc2UgY3g9IjEwMCIgY3k9IjcwIiByeD0iNDAiIHJ5PSIxMCIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgCiAgPCEtLSBPYmplY3Qgc3RvcmFnZSBzeW1ib2xzIC0gY2VudGVyZWQgYW5kIHdpdGggcGVyc3BlY3RpdmUgLS0+CiAgPHJlY3QgeD0iMTA1IiB5PSI5MCIgd2lkdGg9IjEyIiBoZWlnaHQ9IjEyIiBmaWxsPSIjMzMzMzMzIiB0cmFuc2Zvcm09InNrZXdYKC0xMCkiLz4KICA8cmVjdCB4PSIxMjUiIHk9IjkwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIGZpbGw9IiMzMzMzMzMiIHRyYW5zZm9ybT0ic2tld1goLTEwKSIvPgogIDxyZWN0IHg9IjEwNSIgeT0iMTEwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIGZpbGw9IiMzMzMzMzMiIHRyYW5zZm9ybT0ic2tld1goLTEwKSIvPgogIDxyZWN0IHg9IjEyNSIgeT0iMTEwIiB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIGZpbGw9IiMzMzMzMzMiIHRyYW5zZm9ybT0ic2tld1goLTEwKSIvPgogIAogIDwhLS0gTWluSU8gdGV4dCAtLT4KICA8dGV4dCB4PSIxMDAiIHk9IjE3MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSJ3aGl0ZSI+TWluSU88L3RleHQ+Cjwvc3ZnPg==' /> mybucket]
C --> C1
C --> C2
C --> C3
end
C1 <-->|target:// protocol| A
B1 <-->|source:// protocol| A[Client Code]
classDef server fill:#f9f,stroke:#333,stroke-width:4px;
class B,C server;
```


So with both the servers deployed and ready, let's register the `source` and `target` protocol to use in the backup scenario.
"""
#%%
# register `source` protocol that connects to the minio instance
register_custom_fs_protocol(
    'source',
    's3',
    {'key' : 'minio', 'secret' : '123456789', 'endpoint_url' : 'http://localhost:9000'}
)
# register `target` protocol that connects to the real s3
register_custom_fs_protocol(
    'target',
    's3', 
    {'key' : 'minio', 'secret' : '987654321', 'endpoint_url' : 'http://localhost:9002'}
)
#%% [markdown]
"""
And finally we can run the backup.

This may seem a bit weird that we open the file and then use a `with` block,
you can read the docs [here](https://filesystem-spec.readthedocs.io/en/latest/features.html#openfile-instances) to better understand what's happening.
"""
#%%
source = fsspec.open('source://mybucket/example_file')
target = fsspec.open('target://mybucket/backup_file', 'wb')

with (source as source_f, target as target_f):
    target_f.write(source_f.read())

df = pd.read_csv('target://mybucket/backup_file')
df
#%% [markdown]
"""
## Closing Thoughts

So we learned how to use fsspsec to provide a unified access model to many types of filesystems (S3, GCS, FTP, HTTP, etc)
that is useable by a diverse set of analytics libraries (DuckDB, Polars, Pandas, etc.). 

Then we learned how to extend fsspec to inject credentials and configuration into the clients for the filesystems, 
hopefully that can help reduce some boilerplate in your code and cleaner analytics pipelines!

Overall I think the folks working on the fsspec project are doing a great job of implementing a unified storage layer for Python. Go have an
explore of [github.com/fsspec](https://github.com/fsspec) to learn more about this project!

And that's about all I have to show..hope you learned something useful!
<details>
<summary>
Cleanup and dependencies
</summary>
"""
#%%
!docker stop chirpy_donkey nervous_sutherland
!pip list --format=freeze
#%% [markdown]
"""
</details>
"""