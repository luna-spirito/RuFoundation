{
  description = "RuFoundation/scpwiki";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    fenix = {
      url = "github:nix-community/fenix/monthly";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, fenix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        ftml-source = pkgs.stdenv.mkDerivation {
          name = "ftml-source";
          src = ./ftml;
          phases = [ "installPhase" ];
          installPhase = "cp -r $src $out";
          __contentAddressed = true;
        };
        ftml = pkgs.rustPlatform.buildRustPackage {
          pname = "ftml";
          version = "1.0";
          src = ftml-source;
          nativeBuildInputs = [ pkgs.python313 ];
          cargoHash = "sha256-IAduD3fd9TTZ+VCDgvOlmeGYVdk2Wbgh9nVv6QVB2BE=";
        };
        web-js = pkgs.stdenv.mkDerivation rec {
          name = "web";
          src = ./web/js;
          yarnOfflineCache = pkgs.fetchYarnDeps {
            yarnLock = src + "/yarn.lock";
            hash = "sha256-2DYk/p6dlF6d12bvtVrjwKbVxUy4DWRyHYPbHssUM9g=";
          };
          nativeBuildInputs = with pkgs; [
            yarnConfigHook
            yarnBuildHook
            nodejs

          ];
          patchPhase = ''
            substituteInPlace build.ts --replace-fail "../../static" "out"
          '';
          preBuild = ''
            mkdir -p out
          '';
          installPhase = ''
            mv out $out
          '';
        };
        scpwiki-python = pkgs.python313.withPackages (ps: with ps;
          let
            django-jazzmin = buildPythonPackage rec {
              pname = "django-jazzmin";
              version = "3.0.1";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/ad/5b/2f8c4b168e6c41bf1e4b14d787deb23d80f618f0693db913bbe208a4a907/django_jazzmin-3.0.1-py3-none-any.whl";
                sha256 = "sha256-EqCkwdT9CcLu8irPah8DEStRW6aVxZ+qjqgO/IHB8hs=";
              };
              format = "wheel";
              doCheck = false;
              propagatedBuildInputs = [ django_5 ];
            };
            django-auto-prefetch = buildPythonPackage rec {
              pname = "django-auto-prefetch";
              version = "1.11.0";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/db/13/d67914d61510cb4d0dfd889db2689db8ad242ef0959245e2d2e1abce93a8/django_auto_prefetch-1.11.0-py3-none-any.whl";
                sha256 = "sha256-y72QNrx2nLat2QpDWsoHt7Ry7TMK8qh5mGKuYN64tjY=";
              };
              format = "wheel";
              doCheck = false;
              propagatedBuildInputs = [ django_5 ];
            };
            # There's one in nixpkgs, but I failed miserably to override django to _5.
            django_5-guardian = buildPythonPackage rec {
              pname = "django_5-guardian";
              version = "2.4.0";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/a2/25/869df12e544b51f583254aadbba6c1a95e11d2d08edeb9e58dd715112db5/django_guardian-2.4.0-py3-none-any.whl";
                sha256 = "sha256-RAymE1hCfldTI2SLJfg4RznlTDiz1lXIHXXgzQ1htpc=";
              };
              format = "wheel";
              doCheck = false;
              propagatedBuildInputs = [ django_5 ];
            };
            django-solo = buildPythonPackage rec {
              pname = "django-solo";
              version = "2.4.0";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/c3/3a/c5332bb9d3d58e2b6b7ed2a4c09ea2b0b1a8e3c5fe9d8169c0867922b6f4/django_solo-2.4.0-py3-none-any.whl";
                sha256 = "sha256-YunH2SliCmGEhRWDmDN1DKFChABRWVz1yOYX3O/J5c8=";
              };
              format = "wheel";
              doCheck = false;
              propagatedBuildInputs = [ django_5 ];
            };
            persisting-theory = buildPythonPackage rec {
              pname = "persisting-theory";
              version = "1.0";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/89/5d/533442b24abd6be67a332987aebc0ce0fcfe39bfad36564d08f3db375291/persisting_theory-1.0-py3-none-any.whl";
                sha256 = "sha256-c/47oep6tnYyocKS/FyfptPr/Q4q103vpW4xar88jSE=";
              };
              format = "wheel";
              doCheck = false;
            };
            django-dynamic-preferences = buildPythonPackage rec {
              pname = "django-dynamic-preferences";
              version = "1.17.0";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/c5/7e/386a9cb4fdc83bcc33a381842a8e359621c780f24ba820c3080406edaafe/django_dynamic_preferences-1.17.0-py2.py3-none-any.whl";
                sha256 = "sha256-H3ER4BI1tic6QDh4PZKovygmy07ufjJHebLcduPgCwY=";
              };
              format = "wheel";
              doCheck = false;
              propagatedBuildInputs = [ django_5 persisting-theory ];
            };
            django-admin-sortable2 = buildPythonPackage rec {
              pname = "django-admin-sortable2";
              version = "2.3.1";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/c8/77/4396e853c3ee3b1264a2bb23f9b1934194ab750c6ecd30aa194b53dec7b9/django_admin_sortable2-2.3.1-py3-none-any.whl";
                sha256 = "sha256-V4T0QfNTIBNDjDwyJvvMw5uccz+Geyal9HfWsF9zS5M=";
              };
              format = "wheel";
              doCheck = false;
              propagatedBuildInputs = [ django_5 ];
            };
          in with ps; [
            django_5 django-jazzmin django_5-guardian pillow
            python-dotenv psycopg2 watchdog beautifulsoup4
            django-auto-prefetch langcodes requests
            django-solo psutil whitenoise
            gunicorn django-dynamic-preferences django-admin-sortable2
            rcssmin
            (django-debug-toolbar.override { django = django_5; })
          ]
        );
        scpwiki-nofiles = pkgs.stdenv.mkDerivation {
          name = "scpwiki-nofiles";
          src = ./.;
          buildPhase = ''
            export SECRET_KEY=1
            export DEBUG=false
            cp -r ${web-js}/* ./static/
            cp -r ${ftml}/lib/libftml.so ./ftml/ftml.so
            rm -rf files
            ${scpwiki-python}/bin/python3 manage.py collectstatic --noinput
          '';
          installPhase = ''
            cp -r . $out
          '';
        };
      in
        {
          devShells.default = with pkgs; mkShell {
            buildInputs = [
              postgresql
              scpwiki-python
              yarn

              fenix.packages.${system}.minimal.toolchain
            ];
          };
          packages = { inherit ftml web-js scpwiki-python scpwiki-nofiles; };
        }
    );
}
