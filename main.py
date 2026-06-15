from paxos.simulator import Simulator
from paxos.scenarios import load_scenario


HELP = """
Commands:
  help
      Show this help message.

  status
      Show node states and chosen value.

  messages
      Show queued messages.

  start <node> <round> <value>
      Start a proposal.
      Example: start A 1 X

  deliver <message_id>
      Deliver a queued message.
      Example: deliver 3

  drop <message_id>
      Drop a queued message.
      Example: drop 4

  crash <node>
      Crash a node.
      Example: crash B

  recover <node>
      Recover a node.
      Example: recover B

  scenario <name>
      Load a built-in scenario.
      Available:
        happy
        old_accept
        preserve_old_value
        partial_accept

  reset
      Reset simulator.

  quit
      Exit.
"""


def main() -> None:
    sim = Simulator()

    print("Paxos Playground")
    print("Type 'help' to see commands.")
    print()

    while True:
        try:
            raw = input("> ").strip()
        except EOFError:
            print()
            break

        if not raw:
            continue

        parts = raw.split()
        command = parts[0].lower()

        try:
            if command == "help":
                print(HELP)

            elif command == "status":
                sim.print_status()

            elif command == "messages":
                sim.print_messages()

            elif command == "start":
                if len(parts) < 4:
                    print("Usage: start <node> <round> <value>")
                    continue

                proposer = parts[1]
                round_number = int(parts[2])
                value = " ".join(parts[3:])
                sim.start_proposal(proposer, round_number, value)

            elif command == "deliver":
                if len(parts) != 2:
                    print("Usage: deliver <message_id>")
                    continue

                sim.deliver(int(parts[1]))

            elif command == "drop":
                if len(parts) != 2:
                    print("Usage: drop <message_id>")
                    continue

                sim.drop(int(parts[1]))

            elif command == "crash":
                if len(parts) != 2:
                    print("Usage: crash <node>")
                    continue

                sim.crash(parts[1])

            elif command == "recover":
                if len(parts) != 2:
                    print("Usage: recover <node>")
                    continue

                sim.recover(parts[1])

            elif command == "scenario":
                if len(parts) != 2:
                    print("Usage: scenario <name>")
                    continue

                sim = load_scenario(parts[1])
                print(f"Loaded scenario: {parts[1]}")

            elif command == "reset":
                sim = Simulator()
                print("Simulator reset.")

            elif command in {"quit", "exit"}:
                break

            else:
                print(f"Unknown command: {command}")
                print("Type 'help' to see commands.")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()