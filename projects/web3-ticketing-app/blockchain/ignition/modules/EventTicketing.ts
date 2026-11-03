import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const EventTicketing = buildModule("EventTicketingModule", (m) => {
  const eventTicketing = m.contract("EventTicketing");

  return { eventTicketing };
});

export default EventTicketing;
