// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract RockPaperScissors is ReentrancyGuard {
    using SafeERC20 for IERC20;

    enum Move {
        None,
        Rock,
        Paper,
        Scissors
    }

    enum GameState {
        Open,
        Committed,
        Revealed,
        Settled
    }

    struct Game {
        address player1;
        address player2;
        bytes32 p1Commitment;
        bytes32 p2Commitment;
        Move p1Reveal;
        Move p2Reveal;
        uint256 wager;
        GameState state;
        uint256 revealDeadline;
    }

    uint256 public constant FEE_SCALE = 1_000;
    uint256 public constant COMMIT_WINDOW = 5 minutes;
    uint256 public constant REVEAL_WINDOW = 5 minutes;

    IERC20 public immutable usdcToken;
    address public owner;
    uint256 public feePercentage = 15; // 1.5% using FEE_SCALE=1000.
    uint256 public accumulatedFees;

    mapping(uint256 => Game) public games;
    uint256 public gameCounter;

    event GameCreated(uint256 indexed gameId, address indexed player1, uint256 wager);
    event GameJoined(uint256 indexed gameId, address indexed player2);
    event MoveCommitted(uint256 indexed gameId, address indexed player);
    event MoveRevealed(uint256 indexed gameId, address indexed player, Move move);
    event GameSettled(uint256 indexed gameId, address indexed winner, uint256 payout, uint256 fee);
    event GameTied(uint256 indexed gameId);
    event GameCancelled(uint256 indexed gameId);
    event FeePercentageUpdated(uint256 oldFee, uint256 newFee);
    event OwnerChanged(address indexed oldOwner, address indexed newOwner);
    event FeesWithdrawn(address indexed to, uint256 amount);

    error OnlyOwner();
    error InvalidAddress();
    error InvalidWager();
    error InvalidMove();
    error InvalidCommitment();
    error GameNotFound();
    error NotParticipant();
    error InvalidState();
    error AlreadyJoined();
    error AlreadyCommitted();
    error AlreadyRevealed();
    error DeadlineNotReached();
    error CommitMismatch();
    error NoFees();
    error ExcessiveFee();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    modifier gameExists(uint256 gameId) {
        if (games[gameId].player1 == address(0)) revert GameNotFound();
        _;
    }

    constructor(address _usdcToken) {
        if (_usdcToken == address(0)) revert InvalidAddress();
        usdcToken = IERC20(_usdcToken);
        owner = msg.sender;
    }

    function createGame(uint256 wager) external nonReentrant returns (uint256 gameId) {
        if (wager == 0) revert InvalidWager();

        gameId = ++gameCounter;
        games[gameId] = Game({
            player1: msg.sender,
            player2: address(0),
            p1Commitment: bytes32(0),
            p2Commitment: bytes32(0),
            p1Reveal: Move.None,
            p2Reveal: Move.None,
            wager: wager,
            state: GameState.Open,
            revealDeadline: 0
        });

        usdcToken.safeTransferFrom(msg.sender, address(this), wager);
        emit GameCreated(gameId, msg.sender, wager);
    }

    function cancelOpenGame(uint256 gameId) external nonReentrant gameExists(gameId) {
        Game storage game = games[gameId];
        if (game.player1 != msg.sender) revert NotParticipant();
        if (game.state != GameState.Open || game.player2 != address(0)) revert InvalidState();

        game.state = GameState.Settled;
        usdcToken.safeTransfer(game.player1, game.wager);

        emit GameCancelled(gameId);
    }

    function joinGame(uint256 gameId) external nonReentrant gameExists(gameId) {
        Game storage game = games[gameId];
        if (game.state != GameState.Open) revert InvalidState();
        if (game.player2 != address(0)) revert AlreadyJoined();
        if (msg.sender == game.player1) revert InvalidState();

        game.player2 = msg.sender;
        game.revealDeadline = block.timestamp + COMMIT_WINDOW;
        usdcToken.safeTransferFrom(msg.sender, address(this), game.wager);

        emit GameJoined(gameId, msg.sender);
    }

    function commitMove(uint256 gameId, bytes32 commitment) external gameExists(gameId) {
        if (commitment == bytes32(0)) revert InvalidCommitment();
        Game storage game = games[gameId];
        if (game.player2 == address(0)) revert InvalidState();
        if (game.state == GameState.Settled) revert InvalidState();
        if (block.timestamp > game.revealDeadline) revert DeadlineNotReached();

        if (msg.sender == game.player1) {
            if (game.p1Commitment != bytes32(0)) revert AlreadyCommitted();
            game.p1Commitment = commitment;
        } else if (msg.sender == game.player2) {
            if (game.p2Commitment != bytes32(0)) revert AlreadyCommitted();
            game.p2Commitment = commitment;
        } else {
            revert NotParticipant();
        }

        if (game.p1Commitment != bytes32(0) && game.p2Commitment != bytes32(0)) {
            game.state = GameState.Committed;
            game.revealDeadline = block.timestamp + REVEAL_WINDOW;
        }

        emit MoveCommitted(gameId, msg.sender);
    }

    function revealMove(uint256 gameId, Move move, bytes32 salt) external gameExists(gameId) {
        if (move == Move.None || move > Move.Scissors) revert InvalidMove();
        Game storage game = games[gameId];
        if (game.state != GameState.Committed && game.state != GameState.Revealed) revert InvalidState();
        if (block.timestamp > game.revealDeadline) revert DeadlineNotReached();

        bytes32 expectedCommitment = commitmentFor(gameId, msg.sender, move, salt);

        if (msg.sender == game.player1) {
            if (game.p1Reveal != Move.None) revert AlreadyRevealed();
            if (expectedCommitment != game.p1Commitment) revert CommitMismatch();
            game.p1Reveal = move;
        } else if (msg.sender == game.player2) {
            if (game.p2Reveal != Move.None) revert AlreadyRevealed();
            if (expectedCommitment != game.p2Commitment) revert CommitMismatch();
            game.p2Reveal = move;
        } else {
            revert NotParticipant();
        }

        game.state = GameState.Revealed;
        emit MoveRevealed(gameId, msg.sender, move);

        if (game.p1Reveal != Move.None && game.p2Reveal != Move.None) {
            _settleGame(gameId, game);
        }
    }

    function settleGame(uint256 gameId) external nonReentrant gameExists(gameId) {
        Game storage game = games[gameId];
        if (game.state == GameState.Settled) revert InvalidState();
        if (game.p1Reveal == Move.None || game.p2Reveal == Move.None) revert InvalidState();
        _settleGame(gameId, game);
    }

    function forceSettle(uint256 gameId) external nonReentrant gameExists(gameId) {
        Game storage game = games[gameId];
        if (game.state == GameState.Settled) revert InvalidState();
        if (game.player2 == address(0)) revert InvalidState();
        if (game.revealDeadline == 0 || block.timestamp <= game.revealDeadline) revert DeadlineNotReached();

        if (game.p1Reveal != Move.None && game.p2Reveal != Move.None) {
            _settleGame(gameId, game);
            return;
        }

        bool bothCommitted = game.p1Commitment != bytes32(0) && game.p2Commitment != bytes32(0);
        if (bothCommitted) {
            if (game.p1Reveal != Move.None && game.p2Reveal == Move.None) {
                _payoutWinner(gameId, game, game.player1);
            } else if (game.p2Reveal != Move.None && game.p1Reveal == Move.None) {
                _payoutWinner(gameId, game, game.player2);
            } else {
                _refundBoth(gameId, game);
            }
            return;
        }

        if (game.p1Commitment != bytes32(0) && game.p2Commitment == bytes32(0)) {
            _payoutWinner(gameId, game, game.player1);
        } else if (game.p2Commitment != bytes32(0) && game.p1Commitment == bytes32(0)) {
            _payoutWinner(gameId, game, game.player2);
        } else {
            _refundBoth(gameId, game);
        }
    }

    function updateFeePercentage(uint256 newFeePercentage) external onlyOwner {
        if (newFeePercentage > 100) revert ExcessiveFee(); // Max 10%.
        uint256 oldFee = feePercentage;
        feePercentage = newFeePercentage;
        emit FeePercentageUpdated(oldFee, newFeePercentage);
    }

    function setOwner(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert InvalidAddress();
        address oldOwner = owner;
        owner = newOwner;
        emit OwnerChanged(oldOwner, newOwner);
    }

    function withdrawFees(address to, uint256 amount) external onlyOwner nonReentrant {
        if (to == address(0)) revert InvalidAddress();
        if (amount == 0 || amount > accumulatedFees) revert NoFees();

        accumulatedFees -= amount;
        usdcToken.safeTransfer(to, amount);

        emit FeesWithdrawn(to, amount);
    }

    function commitmentFor(uint256 gameId, address player, Move move, bytes32 salt) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(uint8(move), salt, player, gameId));
    }

    function _settleGame(uint256 gameId, Game storage game) internal {
        if (game.p1Reveal == game.p2Reveal) {
            _refundBoth(gameId, game);
            return;
        }

        bool p1Wins = (game.p1Reveal == Move.Rock && game.p2Reveal == Move.Scissors)
            || (game.p1Reveal == Move.Paper && game.p2Reveal == Move.Rock)
            || (game.p1Reveal == Move.Scissors && game.p2Reveal == Move.Paper);

        address winner = p1Wins ? game.player1 : game.player2;
        _payoutWinner(gameId, game, winner);
    }

    function _payoutWinner(uint256 gameId, Game storage game, address winner) internal {
        uint256 pot = game.wager * 2;
        uint256 fee = (pot * feePercentage) / FEE_SCALE;
        uint256 payout = pot - fee;

        game.state = GameState.Settled;
        accumulatedFees += fee;
        usdcToken.safeTransfer(winner, payout);

        emit GameSettled(gameId, winner, payout, fee);
    }

    function _refundBoth(uint256 gameId, Game storage game) internal {
        game.state = GameState.Settled;
        usdcToken.safeTransfer(game.player1, game.wager);
        usdcToken.safeTransfer(game.player2, game.wager);

        emit GameTied(gameId);
    }
}
