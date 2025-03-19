let pkgs = import <nixpkgs> { };
in pkgs.mkShell {
  buildInputs = [ (pkgs.python311.withPackages (p: with p; [ pip arrow ics requests cachetools structlog cherrypy ])) ];
  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python311.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
