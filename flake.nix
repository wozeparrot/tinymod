{
  description = "tinymod: tinygrad's premier discord moderation bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    pyproject-nix,
    uv2nix,
    pyproject-build-systems,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python313;

      workspace = uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};
      overlay = workspace.mkPyprojectOverlay {sourcePreference = "wheel";};

      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages {inherit python;})
        .overrideScope (nixpkgs.lib.composeManyExtensions [
          pyproject-build-systems.overlays.default
          overlay
        ]);

      venv = pythonSet.mkVirtualEnv "tinymod-env" workspace.deps.default;
    in {
      packages.default = venv;

      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          venv
          uv
          sqlite
          sqlite-web
          net-snmp
          ipmitool
        ];
        env = {
          UV_NO_SYNC = "1";
          UV_PYTHON = "${venv}/bin/python";
          UV_PYTHON_DOWNLOADS = "never";
        };
      };
    });
}
