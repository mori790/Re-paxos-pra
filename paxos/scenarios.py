from paxos.message import Prepare, AcceptRequest
from paxos.node import Acceptor
from paxos.simulator import PaxosSimulator
from paxos.types import NodeId, ProposalNumber, Value

def _format_optional(value: object) -> str:
    if value is None:
        return "None"
    return str(value)

def print_acceptor_states(acceptors: list[Acceptor]) -> None:
    print("\nAcceptor states:")
    for acceptor in acceptors:
        print(
            f"{acceptor.node_id}: "
            f"promised={acceptor.promised_number}, "
            f"accepted=({acceptor.accepted_number}, {acceptor.accepted_value})"
        )

def create_three_acceptors() -> list[Acceptor]:
    return [
        Acceptor(node_id=NodeId("A1")),
        Acceptor(node_id=NodeId("A2")),
        Acceptor(node_id=NodeId("A3")),
    ]

def scenario_basic_success() -> None:
    """
    一番シンプルな成功パターン。

    P1 が value A を提案する。
    3台中3台が Promise / Accepted を返す。
    A が chosen になる。
    """

    acceptors = create_three_acceptors()
    
    simulator = PaxosSimulator(acceptors)
    
    print("P1 proposes value A with proposal number 1")
    
    result = simulator.propose(
        proposer_id=NodeId("P1"),
        proposal_number=ProposalNumber(1),
        value=Value("A"),
    )
    
    print("\nResult:")
    print(f"  chosen_value: {result.chosen_value}")
    print(f"  number of promises: {len(result.promises)}")
    print(f"  number of accepted: {len(result.accepted)}")

    print_acceptor_states(acceptors)

def scenario_old_proposal_rejected() -> None:
    """
    古い proposal number が拒否される例。

    まず P1 が proposal number 5 で Prepare する。
    その後、P2 が proposal number 3 で Prepare する。
    3 は 5 より古いので拒否される。
    """

    acceptor = Acceptor(node_id=NodeId("A1"))
    
    print("P1 sends Prepare(5) to A1")
    
    prepare_5 = Prepare(
        proposer_id=NodeId("P1"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(5),
    )

    promise_5 = acceptor.on_prepare(prepare_5)
    print(f"P1 -> A1: {prepare_5}")
    print(f"A1 -> P1: {promise_5}")

    print("\nStep 2: P2 sends old Prepare(3) to A1")
    print("A1 already promised proposal number 5, so proposal number 3 is too old.")

    
    prepare_3 = Prepare(
        proposer_id=NodeId("P2"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(3),
    )
    
    promise_3 = acceptor.on_prepare(prepare_3)
    print(f"P2 -> A1: {prepare_3}")
    print(f"A1 -> P2: {promise_3}")

    print("\nResult:")
    if promise_3 is None:
        print("  Prepare(3) was rejected.")

    print_acceptor_states([acceptor])
    
def scenario_value_is_inherited() -> None:
    """
    Paxosの安全性で一番大事な例。

    1. P1 が proposal number 1 で value A を提案する
    2. A が acceptors に受け入れられる
    3. その後、P2 が proposal number 2 で value B を提案する
    4. しかし Promise の中に accepted_value=A が含まれる
    5. P2 は B ではなく A を引き継ぐ
    """

    acceptors = create_three_acceptors()

    simulator = PaxosSimulator(acceptors)

    print("Step 1: P1 proposes value A with proposal number 1")
    
    result_1 = simulator.propose(
        proposer_id=NodeId("P1"),
        proposal_number=ProposalNumber(1),
        value=Value("A"),
    )
    
    print("\nResult of P1:")
    print(f"  P1 chosen_value: {result_1.chosen_value}")

    print_acceptor_states(acceptors)

    print("\nStep 2: P2 tries to propose value B with proposal number 2")
    print("But acceptors already accepted value A before.")
    print("So P2 must inherit A from Promise messages.")
    
    result_2 = simulator.propose(
        proposer_id=NodeId("P2"),
        proposal_number=ProposalNumber(2),
        value=Value("B"),
    )
    
    print("\nPromises returned to P2:")
    for promise in result_2.promises:
        print(f"  {promise}")

    print("\nResult of P2:")
    print("  P2 wanted to propose: B")
    print(f"  P2 actually chosen_value: {result_2.chosen_value}")

    print_acceptor_states(acceptors)

def scenario_no_majority() -> None:
    """
    Scenario 4:
    多数派が取れない例。

    3台のAcceptorのうち、A1とA2はすでに proposal number 5 に Promise している。
    その後、P1 が proposal number 1 で value A を提案する。

    A1とA2は proposal number 1 を拒否する。
    A3だけが Promise を返す。

    3台の多数派は2台なので、Promiseが1つだけでは先に進めない。
    よって chosen_value は None になる。
    """

    acceptors = create_three_acceptors()

    print("Step 1: A1 and A2 already promise proposal number 5")

    for acceptor in acceptors[:2]:
        prepare_5 = Prepare(
            proposer_id=NodeId("P_old"),
            acceptor_id=acceptor.node_id,
            proposal_number=ProposalNumber(5),
        )

        promise = acceptor.on_prepare(prepare_5)

        print(f"P_old -> {acceptor.node_id}: {prepare_5}")
        print(f"{acceptor.node_id} -> P_old: {promise}")

    print_acceptor_states(acceptors)

    print("\nStep 2: P1 tries to propose value A with old proposal number 1")
    print("A1 and A2 reject it. Only A3 can promise.")

    simulator = PaxosSimulator(acceptors)

    result = simulator.propose(
        proposer_id=NodeId("P1"),
        proposal_number=ProposalNumber(1),
        value=Value("A"),
    )

    print("\nResult:")
    print(f"  chosen_value: {result.chosen_value}")
    print(f"  number of promises: {len(result.promises)}")
    print(f"  majority required: {simulator.majority_size}")

    if result.chosen_value is None:
        print("  No value was chosen because P1 did not receive a majority of promises.")

    print_acceptor_states(acceptors)

def scenario_late_old_message() -> None:
    """
    Scenario 5:
    古いメッセージが遅れて届く例。

    1. P1 が proposal number 1 で Prepare を送る
    2. しかし P1 の AcceptRequest(1, A) は遅延したとする
    3. その間に P2 が proposal number 2 で Prepare を送る
    4. Acceptor は proposal number 2 に Promise する
    5. その後、遅れて P1 の AcceptRequest(1, A) が届く
    6. しかし Acceptor はすでに proposal number 2 に Promise しているので、
       古い AcceptRequest(1, A) を拒否する

    これにより、古いリーダーの遅延メッセージが後から届いても、
    新しいラウンドを壊せないことが分かる。
    """
    acceptor = Acceptor(node_id=NodeId("A1"))

    print("Step 1: P1 sends Prepare(1) to A1")

    prepare_1 = Prepare(
        proposer_id=NodeId("P1"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(1),
    )

    promise_1 = acceptor.on_prepare(prepare_1)

    print(f"P1 -> A1: {prepare_1}")
    print(f"A1 -> P1: {promise_1}")

    print("\nStep 2: P1 creates AcceptRequest(1, A), but it is delayed")

    delayed_accept_request = AcceptRequest(
        proposer_id=NodeId("P1"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(1),
        value=Value("A"),
    )

    print(f"Delayed message: {delayed_accept_request}")

    print("\nStep 3: Before delayed message arrives, P2 sends Prepare(2)")

    prepare_2 = Prepare(
        proposer_id=NodeId("P2"),
        acceptor_id=NodeId("A1"),
        proposal_number=ProposalNumber(2),
    )

    promise_2 = acceptor.on_prepare(prepare_2)

    print(f"P2 -> A1: {prepare_2}")
    print(f"A1 -> P2: {promise_2}")

    print("\nStep 4: Now the delayed old AcceptRequest(1, A) arrives")
    print("But A1 already promised proposal number 2.")
    print("So A1 must reject AcceptRequest(1, A).")

    accepted = acceptor.on_accept_request(delayed_accept_request)

    print(f"P1 -> A1: {delayed_accept_request}")
    print(f"A1 -> P1: {accepted}")

    print("\nResult:")
    if accepted is None:
        print("  The late old AcceptRequest was rejected.")

    print_acceptor_states([acceptor])