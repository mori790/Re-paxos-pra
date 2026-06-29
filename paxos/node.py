from dataclasses import dataclass, field
from typing import Optional

from paxos.message import Prepare, Promise, AcceptRequest, Accepted
from paxos.types import NodeId, ProposalNumber, Value

@dataclass
class Acceptor:
    """
    Paxos の Acceptor。

    Acceptor は以下の3つの状態を持つ。

    promised_number:
        これ以上古い proposal number は受け付けない、という約束。

    accepted_number:
        最後に受け入れた proposal number。

    accepted_value:
        最後に受け入れた value。
    """
    
    node_id: NodeId
    promised_number: Optional[ProposalNumber] = None
    accepted_number: Optional[ProposalNumber] = None
    accepted_value: Optional[Value] = None
    
    def on_prepare(self, message: Prepare) -> Optional[Promise]:
        """
        Prepare メッセージを受け取ったときの処理。

        新しい proposal number なら Promise を返す。
        古い proposal number なら None を返して拒否する。
        """

        if message.acceptor_id != self.node_id:
            return None
        if self.promised_number is not None:
            if message.proposal_number < self.promised_number:
                return None
        
        self.promised_number = message.proposal_number
        
        return Promise(
            acceptor_id=self.node_id,
            proposer_id=message.proposer_id,
            proposal_number=message.proposal_number,
            accepted_number=self.accepted_number,
            accepted_value=self.accepted_value,
        )
    
    def on_accept_request(self, message: AcceptRequest) -> Optional[Accepted]:
        """
        AcceptRequest メッセージを受け取ったときの処理。

        proposal number が promised_number 以上なら受け入れる。
        promised_number より古ければ拒否する。
        """
        
        if message.acceptor_id != self.node_id:
            return None
        
        if self.promised_number is not None:
            if message.proposal_number < self.promised_number:
                return None
            
        self.promised_number = message.proposal_number
        self.accepted_number = message.proposal_number
        self.accepted_value = message.value
        
        return Accepted(
            acceptor_id=self.node_id,
            proposer_id=message.proposer_id,
            proposal_number=message.proposal_number,
            value=message.value,
        )
        
@dataclass
class Proposer:
    """
    Paxos の Proposer。

    Proposer は以下を行う。

    1. Prepare を作る
    2. Promise を集める
    3. Promise の中から最終的に提案する value を決める
    4. AcceptRequest を作る
    5. Accepted を集める
    """
    
    node_id: NodeId
    proposal_number: ProposalNumber
    origin_value: Value
    promises: list[Promise] = field(default_factory=list)
    accepted: list[Accepted] = field(default_factory=list)
    
    def create_prepare(self, acceptor_id: NodeId) -> Prepare:
        """
        指定した Acceptor 宛ての Prepare メッセージを作る。
        """
        
        return Prepare(
            proposer_id=self.node_id,
            acceptor_id=acceptor_id,
            proposal_number=self.proposal_number,
        )
    
    def receive_promise(self, promise: Promise) -> None:
        """
        Acceptor から返ってきた Promise を保存する。
        """

        if promise.proposer_id != self.node_id:
            return 
        
        if promise.proposal_number != self.proposal_number:
            return
        
        self.promises.append(promise)
        
    def has_majority_promises(self, majority_size: int) -> bool:
        """
        Promise が多数派に達したか確認する。
        """

        return len(self.promises) >= majority_size
    

    def select_value(self) -> Value:
        """
        Promise を見て、最終的に提案する value を選ぶ。

        ルール:
        - Promise の中に accepted_value がなければ original_value を使う
        - accepted_value があれば、
          accepted_number が一番大きいものの value を引き継ぐ
        """
        
        promises_with_accepted_value = [
            promise
            for promise in self.promises
            if promise.accepted_number is not None
            and promise.accepted_value is not None
        ]
        
        if len(promises_with_accepted_value) == 0:
            return self.origin_value
        
        latest_promise = max(
            promises_with_accepted_value,
            key=lambda promise: promise.accepted_number,
        )
        
        return latest_promise.accepted_value
    
    def create_accept_request(
        self,
        acceptor_id: NodeId,
        value: Value,
    ) -> AcceptRequest:
        """
        指定した Acceptor 宛ての AcceptRequest メッセージを作る。
        """
        
        return AcceptRequest(
            proposer_id=self.node_id,
            acceptor_id=acceptor_id,
            proposal_number=self.proposal_number,
            value=value,
        )

    def receive_accepted(self, accepted: Accepted) -> None:
        """
        Acceptor から返ってきた Accepted を保存する。
        """

        if accepted.proposer_id != self.node_id:
            return

        if accepted.proposal_number != self.proposal_number:
            return

        self.accepted.append(accepted)

    def has_majority_accepted(self, majority_size: int) -> bool:
        """
        Accepted が多数派に達したか確認する。
        """

        return len(self.accepted) >= majority_size
        
