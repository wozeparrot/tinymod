{
  description = "tinymod: tinygrad's premier discord moderation bot";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    poetry2nix,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication mkPoetryEnv defaultPoetryOverrides;
    in {
      packages = {
        myapp = mkPoetryApplication {projectDir = self;};
        default = self.packages.${system}.myapp;
      };

      devShells.default = (mkPoetryEnv {
        projectDir = ./.;
        extraPackages = p: with p; [
          setuptools
        ];
        overrides = defaultPoetryOverrides.extend (self: super: {
          scarletio = super.scarletio.overridePythonAttrs (old: {
            propagatedBuildInputs = (old.propagatedBuildInputs or [ ])
              ++ [ super.setuptools ];
          });
          pygal = super.pygal.overridePythonAttrs (old: {
            propagatedBuildInputs = (old.propagatedBuildInputs or [ ])
              ++ [ super.pytest-runner ];
          });
          hata = super.hata.overridePythonAttrs {
            # remove the `hata.discord.bin` subpackage
            postPatch = ''
              substituteInPlace setup.py --replace "'hata.discord.bin'," ""
            '';
          };
          pygithub = super.pygithub.overridePythonAttrs (old: {
            propagatedBuildInputs = (old.propagatedBuildInputs or [ ])
              ++ [ super.setuptools-scm ];
          });
        });
      }).env.overrideAttrs (old: {
        buildInputs = with pkgs; [
          poetry
          sqlite
          sqlite-web
        ];
      });
    });
}
