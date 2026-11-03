import { expect } from "chai";
import { ethers } from "hardhat";
import type { EventTicketing } from "../typechain-types";
import { time } from "@nomicfoundation/hardhat-network-helpers";

describe("EventTicketing", function () {
  let contract: EventTicketing;
  let owner: any, organizer: any, user1: any, user2: any;

  beforeEach(async () => {
    [owner, organizer, user1, user2] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("EventTicketing");
    contract = await Factory.deploy();
    await contract.waitForDeployment();
  });

  it("should allow organizer to create an event", async () => {
    await contract
      .connect(organizer)
      .createEvent("Coldplay", ethers.parseEther("0.05"), 2, false);
    const ev = await contract.events(1);
    expect(ev.name).to.equal("Coldplay");
    expect(ev.totalTickets).to.equal(2);
    expect(ev.organizer).to.equal(organizer.address);
  });

  it("should allow user to mint ticket with correct price", async () => {
    await contract
      .connect(organizer)
      .createEvent("Coldplay", ethers.parseEther("0.05"), 2, false);
    await contract
      .connect(user1)
      .mintTicket(1, "ipfs://metadata", { value: ethers.parseEther("0.05") });
    const ownerOf = await contract.ownerOf(1);
    expect(ownerOf).to.equal(user1.address);
  });

  it("should revert mint if not enough ETH", async () => {
    await contract
      .connect(organizer)
      .createEvent("Coldplay", ethers.parseEther("0.05"), 2, false);
    await expect(
      contract
        .connect(user1)
        .mintTicket(1, "ipfs://metadata", { value: ethers.parseEther("0.01") })
    ).to.be.revertedWith("Not enough ETH");
  });

  it("should record event revenue correctly and allow withdrawal", async () => {
    await contract
      .connect(organizer)
      .createEvent("Coldplay", ethers.parseEther("1.0"), 1, false);
    await contract
      .connect(user1)
      .mintTicket(1, "ipfs://metadata", { value: ethers.parseEther("1.0") });

    const revenue = await contract.getEventRevenue(1);
    expect(revenue).to.equal(ethers.parseEther("1.0"));

    const before = await ethers.provider.getBalance(organizer.address);
    const tx = await contract.connect(organizer).withdrawEventRevenue(1);
    const receipt = await tx.wait();
    const gasUsed = receipt!.gasUsed * receipt!.gasPrice!;
    const after = await ethers.provider.getBalance(organizer.address);

    // ✅ 修正：使用 BigInt 比較
    expect(after).to.be.closeTo(
      before + BigInt(ethers.parseEther("1.0").toString()) - gasUsed,
      BigInt(1e15) // 允許最多 0.001 ETH 誤差
    );
  });

  it("should reject withdrawal by non-organizer", async () => {
    await contract
      .connect(organizer)
      .createEvent("Coldplay", ethers.parseEther("1.0"), 1, false);
    await expect(
      contract.connect(user1).withdrawEventRevenue(1)
    ).to.be.revertedWith("Not the organizer");
  });

  it("should enforce SBT: cannot transfer", async () => {
    await contract
      .connect(organizer)
      .createEvent("SBT Event", ethers.parseEther("0.01"), 1, true);
    await contract
      .connect(user1)
      .mintTicket(1, "ipfs://metadata", { value: ethers.parseEther("0.01") });

    await expect(
      contract.connect(user1).transferFrom(user1.address, user2.address, 1)
    ).to.be.revertedWith("SBT: transfer not allowed");
  });

  it("should allow ticket listing and buying", async () => {
    await contract
      .connect(organizer)
      .createEvent("Market", ethers.parseEther("0.01"), 1, false);
    await contract
      .connect(user1)
      .mintTicket(1, "ipfs://metadata", { value: ethers.parseEther("0.01") });

    await contract.connect(user1).listTicket(1, ethers.parseEther("0.02"));
    await contract
      .connect(user2)
      .buyListedTicket(1, { value: ethers.parseEther("0.02") });

    expect(await contract.ownerOf(1)).to.equal(user2.address);
  });

  it("should prevent listing a checked-in ticket", async () => {
    await contract
      .connect(organizer)
      .createEvent("CheckIn", ethers.parseEther("0.01"), 1, false);
    await contract
      .connect(user1)
      .mintTicket(1, "ipfs://metadata", { value: ethers.parseEther("0.01") });

    const timestamp = await time.latest();
    const message = `Check-in ticketId: 1 at ${timestamp}`;
    const sig = await user1.signMessage(message);

    await contract
      .connect(organizer)
      .checkInByOrganizer(1, 1, message, sig, timestamp);

    await expect(
      contract.connect(user1).listTicket(1, ethers.parseEther("0.01"))
    ).to.be.revertedWith("Checked-in ticket can't be listed");
  });

  it("should return correct ticket holders", async () => {
    await contract
      .connect(organizer)
      .createEvent("Multiple", ethers.parseEther("0.05"), 2, false);
    await contract
      .connect(user1)
      .mintTicket(1, "ipfs://a", { value: ethers.parseEther("0.05") });
    await contract
      .connect(user2)
      .mintTicket(1, "ipfs://b", { value: ethers.parseEther("0.05") });

    const holders = await contract.getEventTicketHolders(1);
    expect(holders).to.include.members([user1.address, user2.address]);
  });
});
