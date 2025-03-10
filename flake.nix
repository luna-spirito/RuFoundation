{
  description = "RuFoundation/scpwiki/24.11";

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
          nativeBuildInputs = [ pkgs.python311 ];
          cargoHash = "sha256-1mbD7yCRhmvO+B02pPK3Y+hYB5tQNfLeywycDeFOCMc=";
        };
        mk-js = n: hash: pkgs.stdenv.mkDerivation rec {
          name = n;
          src = ./${n}/js;
          yarnOfflineCache = pkgs.fetchYarnDeps {
            yarnLock = src + "/yarn.lock";
            inherit hash;
          };
          nativeBuildInputs = with pkgs; [
            yarnConfigHook
            yarnBuildHook
            nodePackages_latest.ts-node
          ];

          installPhase = ''
            mv out $out
          '';
        };
        web-js = mk-js "web" "sha256-1fkXoO5z2stM8q5QWEnqKgE2tqail3NFgPM6vE854EY=";
        system-js = mk-js "system" "sha256-1fkXoO5z2stM8q5QWEnqKgE2tqail3NFgPM6vE854EY=";
        scpwiki-python = pkgs.python311.withPackages (ps: with ps;
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
            django-cockroachdb = buildPythonPackage rec {
              pname = "django-cockroachdb";
              version = "5.1";
              src = pkgs.fetchurl {
                url = "https://files.pythonhosted.org/packages/b2/5a/c44c2dd79be313d8d51bb4bacfa8844d102152383316e784658c640956c7/django_cockroachdb-5.1-py3-none-any.whl";
                sha256 = "sha256-nLitArnp6n1+coS5AqcPskVfptmL+0DsIiFxrCA6juc=";
              };
              format = "wheel";
              doCheck = false;
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
          in with ps; [
            django_5 django-jazzmin django_5-guardian pillow
            django-cockroachdb python-dotenv psycopg2 watchdog
            beautifulsoup4 django-auto-prefetch langcodes requests
            django-solo psutil whitenoise
            gunicorn
          ]
        );
        scpwiki-nofiles = pkgs.stdenv.mkDerivation {
          name = "scpwiki-nofiles";
          src = ./.;
          buildPhase = ''
            cp -r ${web-js}/* ./static/
            cp -r ${system-js}/* ./static/
            cp -r ${ftml}/lib/libftml.so ./ftml/ftml.so
            rm -rf files
            ${scpwiki-python}/bin/python3 manage.py collectstatic
          '';
          installPhase = ''
            cp -r . $out
          '';
        };
        devShell = with-cockroach: with pkgs; mkShell {
          buildInputs = [
            scpwiki-python
            yarn
            nodePackages_latest.ts-node
            fenix.packages.${system}.minimal.toolchain
            (writeScriptBin "cockroach-insecure-start" ./cockroach-insecure-start.sh)
            (writeScriptBin "cockroach-insecure-reset" ./cockroach-insecure-reset.sh)
          ] ++ lib.optional with-cockroach [ cockroachdb ];
        };
      in
        {
          devShells = {
            with-cockroach = devShell true;
            default = devShell false;
          };
          packages = { inherit ftml scpwiki-python scpwiki-nofiles; };
        }
    );
}
