{ pkgs ? import <nixpkgs> {} }:

with pkgs.python3Packages;

pkgs.mkShell {
  name = "python${python.pythonVersion}-environment";
  strictDeps = true;
  nativeBuildInputs = [ pkgs.curl uvicorn pytest ];
  buildInputs = [ aiosqlite databases fastapi sqlalchemy pytest-asyncio mock ];

  shellHook = ''
    prefix=$PWD/inst
    export PATH=$prefix/bin:$PATH
    export PYTHONPATH=$prefix/lib/python${python.pythonVersion}/site-packages:$PYTHONPATH

    mkdir -p $prefix/lib/python${python.pythonVersion}/site-packages
    python3 setup.py develop --prefix=$prefix --allow-hosts None --no-deps &> /dev/null
  '';
}
