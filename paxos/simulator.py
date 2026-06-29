# paxos/simulator.py

from dataclasses import dataclass
from typing import Optional

from paxos.message import Accepted, Promise
from paxos.node import Acceptor, Proposer
from paxos.types import NodeId, ProposalNumber, Value


@dataclass
class PaxosResult:
    """
    Paxosの1回の提案結果。

    chosen_value:
        多数派に受け入れられて決定された値。
        失敗した場合は None。

    promises:
        Prepareに対して返ってきたPromise一覧。

    accepted:
        AcceptRequestに対して返ってきたAccepted一覧。
    """

    chosen_value: Optional[Value]
    promises: list[Promise]
    accepted: list[Accepted]


class PaxosSimulator:
    """
    教育用のシンプルなPaxosシミュレータ。

    Simulator 自体はPaxosの判断を持ちすぎない。
    Proposer と Acceptor のメッセージ交換を進める役割にする。
    """

    def __init__(self, acceptors: list[Acceptor]) -> None:
        if len(acceptors) == 0:
            raise ValueError("At least one acceptor is required.")

        self.acceptors = acceptors

    @property
    def majority_size(self) -> int:
        """
        多数派に必要な数。

        例:
            3台なら2
            5台なら3
        """

        return len(self.acceptors) // 2 + 1

    def propose(
        self,
        proposer_id: NodeId,
        proposal_number: ProposalNumber,
        value: Value,
    ) -> PaxosResult:
        """
        1つの値をPaxosで提案する。

        Phase 1:
            Proposer が Prepare を作る。
            Acceptor が Promise を返す。
            Proposer が Promise を保存する。

        Phase 2:
            Proposer が AcceptRequest を作る。
            Acceptor が Accepted を返す。
            Proposer が Accepted を保存する。

        多数派の Accepted が集まったら chosen。
        """

        proposer = Proposer(
            node_id=proposer_id,
            proposal_number=proposal_number,
            origin_value=value,
        )

        self._run_prepare_phase(proposer)

        if not proposer.has_majority_promises(self.majority_size):
            return PaxosResult(
                chosen_value=None,
                promises=proposer.promises,
                accepted=[],
            )

        selected_value = proposer.select_value()

        self._run_accept_phase(
            proposer=proposer,
            value=selected_value,
        )

        if not proposer.has_majority_accepted(self.majority_size):
            return PaxosResult(
                chosen_value=None,
                promises=proposer.promises,
                accepted=proposer.accepted,
            )

        return PaxosResult(
            chosen_value=selected_value,
            promises=proposer.promises,
            accepted=proposer.accepted,
        )

    def _run_prepare_phase(self, proposer: Proposer) -> None:
        """
        Phase 1: Prepare / Promise

        Proposer が各 Acceptor に Prepare を送り、
        返ってきた Promise を保存する。
        """

        for acceptor in self.acceptors:
            prepare = proposer.create_prepare(acceptor_id=acceptor.node_id)

            print(f"{proposer.node_id} -> {acceptor.node_id}: {prepare}")

            promise = acceptor.on_prepare(prepare)

            if promise is None:
                print(f"{acceptor.node_id} -> {proposer.node_id}: rejected Prepare")
                continue

            print(f"{acceptor.node_id} -> {proposer.node_id}: {promise}")

            proposer.receive_promise(promise)

    def _run_accept_phase(
        self,
        proposer: Proposer,
        value: Value,
    ) -> None:
        """
        Phase 2: AcceptRequest / Accepted

        Proposer が各 Acceptor に AcceptRequest を送り、
        返ってきた Accepted を保存する。
        """

        for acceptor in self.acceptors:
            accept_request = proposer.create_accept_request(
                acceptor_id=acceptor.node_id,
                value=value,
            )

            print(f"{proposer.node_id} -> {acceptor.node_id}: {accept_request}")

            accepted = acceptor.on_accept_request(accept_request)

            if accepted is None:
                print(f"{acceptor.node_id} -> {proposer.node_id}: rejected AcceptRequest")
                continue

            print(f"{acceptor.node_id} -> {proposer.node_id}: {accepted}")

            proposer.receive_accepted(accepted)