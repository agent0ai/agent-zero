const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("RockPaperScissors", function () {
  async function deployFixture() {
    const [owner, alice, bob] = await ethers.getSigners();

    const usdc = await ethers.deployContract("MockUSDC");
    await usdc.waitForDeployment();

    const game = await ethers.deployContract("RockPaperScissors", [await usdc.getAddress()]);
    await game.waitForDeployment();

    const initialFunds = ethers.parseUnits("1000", 6);
    await usdc.mint(alice.address, initialFunds);
    await usdc.mint(bob.address, initialFunds);

    await usdc.connect(alice).approve(await game.getAddress(), initialFunds);
    await usdc.connect(bob).approve(await game.getAddress(), initialFunds);

    return { owner, alice, bob, usdc, game };
  }

  function commitmentFor(move, salt, player, gameId) {
    return ethers.solidityPackedKeccak256(
      ["uint8", "bytes32", "address", "uint256"],
      [move, salt, player, gameId]
    );
  }

  async function createAndJoin(game, alice, bob, wager) {
    await game.connect(alice).createGame(wager);
    const gameId = await game.gameCounter();
    await game.connect(bob).joinGame(gameId);
    return gameId;
  }

  it("pays winner and tracks 1.5% service fee", async function () {
    const { alice, bob, usdc, game } = await deployFixture();
    const wager = ethers.parseUnits("10", 6);
    const gameId = await createAndJoin(game, alice, bob, wager);

    const salt1 = ethers.keccak256(ethers.toUtf8Bytes("salt-alice"));
    const salt2 = ethers.keccak256(ethers.toUtf8Bytes("salt-bob"));
    const c1 = commitmentFor(1, salt1, alice.address, gameId);
    const c2 = commitmentFor(3, salt2, bob.address, gameId);

    await game.connect(alice).commitMove(gameId, c1);
    await game.connect(bob).commitMove(gameId, c2);

    await game.connect(alice).revealMove(gameId, 1, salt1);
    await game.connect(bob).revealMove(gameId, 3, salt2);

    const aliceExpected = ethers.parseUnits("1009.7", 6);
    const bobExpected = ethers.parseUnits("990", 6);
    const expectedFees = ethers.parseUnits("0.3", 6);

    expect(await usdc.balanceOf(alice.address)).to.equal(aliceExpected);
    expect(await usdc.balanceOf(bob.address)).to.equal(bobExpected);
    expect(await game.accumulatedFees()).to.equal(expectedFees);
  });

  it("refunds both players on tie with zero fee", async function () {
    const { alice, bob, usdc, game } = await deployFixture();
    const wager = ethers.parseUnits("10", 6);
    const gameId = await createAndJoin(game, alice, bob, wager);

    const salt1 = ethers.keccak256(ethers.toUtf8Bytes("tie-1"));
    const salt2 = ethers.keccak256(ethers.toUtf8Bytes("tie-2"));
    const c1 = commitmentFor(1, salt1, alice.address, gameId);
    const c2 = commitmentFor(1, salt2, bob.address, gameId);

    await game.connect(alice).commitMove(gameId, c1);
    await game.connect(bob).commitMove(gameId, c2);
    await game.connect(alice).revealMove(gameId, 1, salt1);
    await game.connect(bob).revealMove(gameId, 1, salt2);

    expect(await usdc.balanceOf(alice.address)).to.equal(ethers.parseUnits("1000", 6));
    expect(await usdc.balanceOf(bob.address)).to.equal(ethers.parseUnits("1000", 6));
    expect(await game.accumulatedFees()).to.equal(0);
  });

  it("force settles reveal timeout when only one reveal is submitted", async function () {
    const { owner, alice, bob, usdc, game } = await deployFixture();
    const wager = ethers.parseUnits("10", 6);
    const gameId = await createAndJoin(game, alice, bob, wager);

    const salt1 = ethers.keccak256(ethers.toUtf8Bytes("reveal-timeout-1"));
    const salt2 = ethers.keccak256(ethers.toUtf8Bytes("reveal-timeout-2"));
    const c1 = commitmentFor(2, salt1, alice.address, gameId);
    const c2 = commitmentFor(3, salt2, bob.address, gameId);

    await game.connect(alice).commitMove(gameId, c1);
    await game.connect(bob).commitMove(gameId, c2);

    await game.connect(alice).revealMove(gameId, 2, salt1);
    await time.increase(5 * 60 + 1);
    await game.connect(owner).forceSettle(gameId);

    expect(await usdc.balanceOf(alice.address)).to.equal(ethers.parseUnits("1009.7", 6));
    expect(await usdc.balanceOf(bob.address)).to.equal(ethers.parseUnits("990", 6));
    expect(await game.accumulatedFees()).to.equal(ethers.parseUnits("0.3", 6));
  });

  it("force settles commit timeout when only one player committed", async function () {
    const { owner, alice, bob, usdc, game } = await deployFixture();
    const wager = ethers.parseUnits("10", 6);
    const gameId = await createAndJoin(game, alice, bob, wager);

    const salt1 = ethers.keccak256(ethers.toUtf8Bytes("commit-timeout-1"));
    const c1 = commitmentFor(3, salt1, alice.address, gameId);
    await game.connect(alice).commitMove(gameId, c1);

    await time.increase(5 * 60 + 1);
    await game.connect(owner).forceSettle(gameId);

    expect(await usdc.balanceOf(alice.address)).to.equal(ethers.parseUnits("1009.7", 6));
    expect(await usdc.balanceOf(bob.address)).to.equal(ethers.parseUnits("990", 6));
    expect(await game.accumulatedFees()).to.equal(ethers.parseUnits("0.3", 6));
  });
});
