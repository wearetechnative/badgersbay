{
  description = "Honeybadger Server - Security report aggregation server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python met dependencies
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pyyaml
        ]);

        # Helper script om de server te starten
        startServer = pkgs.writeShellScriptBin "honeybadger-server" ''
          cd "$(dirname "$(readlink -f "$0")")/.."
          exec ${pythonEnv}/bin/python honeybadger_server.py "$@"
        '';

        # Helper script om tests te draaien
        runTests = pkgs.writeShellScriptBin "honeybadger-test" ''
          cd "$(dirname "$(readlink -f "$0")")/.."
          exec ./test.sh
        '';

      in
      {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.curl        # Voor testen
            pkgs.jq          # Voor JSON parsing
            startServer
            runTests
          ];

          shellHook = ''
            echo "🦡 Honeybadger Server Development Environment"
            echo ""
            echo "Available commands:"
            echo "  honeybadger-server  - Start de server"
            echo "  honeybadger-test    - Run test suite"
            echo "  python              - Python ${pythonEnv.python.version} met PyYAML"
            echo ""
            echo "Server configuratie: config.yaml"
            echo "Server script: honeybadger_server.py"
            echo ""
          '';
        };

        # Package voor de server zelf
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "honeybadger-server";
          version = "1.0.0";
          src = ./.;

          buildInputs = [ pythonEnv ];

          installPhase = ''
            mkdir -p $out/bin $out/share/honeybadger-server

            # Kopieer de server script
            cp honeybadger_server.py $out/share/honeybadger-server/
            cp config.yaml $out/share/honeybadger-server/

            # Maak wrapper script
            cat > $out/bin/honeybadger-server <<EOF
            #!${pkgs.bash}/bin/bash
            cd $out/share/honeybadger-server
            exec ${pythonEnv}/bin/python honeybadger_server.py "\$@"
            EOF
            chmod +x $out/bin/honeybadger-server
          '';

          meta = with pkgs.lib; {
            description = "Centralized security report aggregation server";
            license = licenses.mit;
            platforms = platforms.linux ++ platforms.darwin;
          };
        };

        # App definitie voor 'nix run'
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/honeybadger-server";
        };
      }
    );
}
