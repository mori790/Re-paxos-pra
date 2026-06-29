# main.py

from paxos.message import Prepare, AcceptRequest
from paxos.node import Acceptor
from paxos.types import NodeId, ProposalNumber, Value
from paxos.scenarios import (
    scenario_basic_success,
    scenario_late_old_message,
    scenario_no_majority,
    scenario_old_proposal_rejected,
    scenario_value_is_inherited,
)

def main() -> None:
    acceptor = Acceptor(node_id=NodeId("A1"))

    prepare = Prepare(
        proposer_id=NodeId("P1"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(1),
    )

    promise = acceptor.on_prepare(prepare)
    print("Promise:", promise)

    accept_request = AcceptRequest(
        proposer_id=NodeId("P1"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(1),
        value=Value("A"),
    )

    accepted = acceptor.on_accept_request(accept_request)
    print("Accepted:", accepted)

    old_prepare = Prepare(
        proposer_id=NodeId("P2"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(0),
    )

    old_promise = acceptor.on_prepare(old_prepare)
    print("Old Promise:", old_promise)

    print("Acceptor state:", acceptor)

    print("\n==============================")
    print("Scenario 1: Basic Success")
    print("==============================")
    scenario_basic_success()

    print("\n==============================")
    print("Scenario 2: Old Proposal Rejected")
    print("==============================")
    scenario_old_proposal_rejected()

    print("\n==============================")
    print("Scenario 3: Value Is Inherited")
    print("==============================")
    scenario_value_is_inherited()

    print("\n==============================")
    print("Scenario 4: No Majority")
    print("==============================")
    scenario_no_majority()

    print("\n==============================")
    print("Scenario 5: Late Old Message")
    print("==============================")
    scenario_late_old_message()

if __name__ == "__main__":
    main()