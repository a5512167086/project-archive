// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract EventTicketing is ERC721, ERC721Enumerable, Ownable {
    uint256 public eventIdCounter = 1;
    uint256 public ticketIdCounter = 1;
    uint256 public constant SIGNATURE_EXPIRY = 300;

    struct Event {
        address organizer;
        uint256 ticketPrice;
        uint256 totalTickets;
        uint256 ticketsSold;
        string name;
        bool active;
        bool isSoulBound;
        uint256[] ticketIds;
    }

    struct Listing {
        address seller;
        uint256 price;
        bool active;
    }

    mapping(uint256 => Event) public events;
    mapping(uint256 => uint256) public ticketToEvent;
    mapping(uint256 => uint256) public checkedInAt;
    mapping(uint256 => string) private _tokenURIs;
    mapping(uint256 => Listing) public listings;
    mapping(uint256 => uint256) public eventRevenue;

    event TicketListed(uint256 ticketId, address seller, uint256 price);
    event TicketSold(uint256 ticketId, address buyer, uint256 price);
    event TicketDelisted(uint256 ticketId, address seller);

    constructor() ERC721("Web3Ticketing", "W3T") Ownable(msg.sender) {}

    // 🟡 建立活動（由主辦方呼叫）
    function createEvent(
        string memory name,
        uint256 ticketPrice,
        uint256 totalTickets,
        bool isSoulBound
    ) external {
        require(ticketPrice > 0, "Invalid price");
        require(totalTickets > 0, "Must have tickets");

        uint256 newEventId = eventIdCounter++;
        events[newEventId] = Event({
            organizer: msg.sender,
            ticketPrice: ticketPrice,
            totalTickets: totalTickets,
            ticketsSold: 0,
            name: name,
            active: true,
            isSoulBound: isSoulBound,
            ticketIds: new uint256[](0) // ✅ 正確初始化空陣列
        });
    }

    // 🟢 使用者 mint 票券（提供 metadata URI）
    function mintTicket(
        uint256 eventId,
        string memory metadataURI
    ) external payable {
        Event storage ev = events[eventId];
        require(ev.active, "Event not active");
        require(ev.ticketsSold < ev.totalTickets, "All tickets sold");
        require(msg.value >= ev.ticketPrice, "Not enough ETH");

        uint256 newTicketId = ticketIdCounter++;
        _safeMint(msg.sender, newTicketId);
        _setTokenURI(newTicketId, metadataURI);

        ev.ticketIds.push(newTicketId);
        ev.ticketsSold++;
        ticketToEvent[newTicketId] = eventId;
        eventRevenue[eventId] += msg.value;
    }

    function getEventTicketIds(
        uint256 eventId
    ) external view returns (uint256[] memory) {
        return events[eventId].ticketIds;
    }

    function getEventTicketHolders(
        uint256 eventId
    ) external view returns (address[] memory) {
        Event storage ev = events[eventId];
        address[] memory holders = new address[](ev.ticketIds.length);
        for (uint256 i = 0; i < ev.ticketIds.length; i++) {
            holders[i] = ownerOf(ev.ticketIds[i]);
        }
        return holders;
    }

    function getEventRevenue(uint256 eventId) external view returns (uint256) {
        return eventRevenue[eventId];
    }

    function withdrawEventRevenue(uint256 eventId) external {
        Event storage ev = events[eventId];
        require(msg.sender == ev.organizer, "Not the organizer");

        uint256 amount = eventRevenue[eventId];
        require(amount > 0, "No revenue");

        eventRevenue[eventId] = 0;
        payable(msg.sender).transfer(amount);
    }

    // ✅ 驗票邏輯（主辦方檢查是否持有人簽章過）
    function checkInByOrganizer(
        uint256 expectedEventId,
        uint256 ticketId,
        string memory message,
        bytes memory signature,
        uint256 timestamp
    ) external {
        uint256 actualEventId = ticketToEvent[ticketId];
        require(expectedEventId == actualEventId, "Event mismatch");

        Event storage ev = events[actualEventId];
        require(msg.sender == ev.organizer, "Not organizer");
        require(checkedInAt[ticketId] == 0, "Already checked in");
        require(
            block.timestamp <= timestamp + SIGNATURE_EXPIRY,
            "Signature expired"
        );

        string memory expectedMessage = string(
            abi.encodePacked(
                "Check-in ticketId: ",
                _uintToString(ticketId),
                " at ",
                _uintToString(timestamp)
            )
        );

        require(
            keccak256(abi.encodePacked(message)) ==
                keccak256(abi.encodePacked(expectedMessage)),
            "Invalid message format"
        );

        address signer = getSigner(message, signature);
        require(signer == ownerOf(ticketId), "Signature not from owner");

        checkedInAt[ticketId] = block.timestamp;
    }

    function getCheckInTimestamp(
        uint256 ticketId
    ) external view returns (uint256) {
        return checkedInAt[ticketId];
    }

    function setEventActive(uint256 eventId, bool isActive) external {
        Event storage ev = events[eventId];
        require(msg.sender == ev.organizer, "Not organizer");
        ev.active = isActive;
    }

    // 🔒 SBT 控制（不能轉讓）
    function isTicketSoulBound(uint256 ticketId) public view returns (bool) {
        uint256 eventId = ticketToEvent[ticketId];
        return events[eventId].isSoulBound;
    }

    function _update(
        address to,
        uint256 tokenId,
        address auth
    ) internal override(ERC721, ERC721Enumerable) returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) {
            require(!isTicketSoulBound(tokenId), "SBT: transfer not allowed");
        }
        return super._update(to, tokenId, auth);
    }

    // 🏷️ 二手交易
    function listTicket(uint256 ticketId, uint256 price) external {
        require(ownerOf(ticketId) == msg.sender, "Not owner");
        require(!isTicketSoulBound(ticketId), "SBT: cannot list");
        require(
            checkedInAt[ticketId] == 0,
            "Checked-in ticket can't be listed"
        );
        require(price > 0, "Price must be > 0");

        listings[ticketId] = Listing({
            seller: msg.sender,
            price: price,
            active: true
        });
        emit TicketListed(ticketId, msg.sender, price);
    }

    function cancelListing(uint256 ticketId) external {
        Listing storage listing = listings[ticketId];
        require(listing.active, "Not listed");
        require(listing.seller == msg.sender, "Not seller");

        listing.active = false;
        emit TicketDelisted(ticketId, msg.sender);
    }

    function buyListedTicket(uint256 ticketId) external payable {
        Listing storage listing = listings[ticketId];
        require(listing.active, "Not listed");
        require(msg.value >= listing.price, "Insufficient ETH");
        require(ownerOf(ticketId) == listing.seller, "Seller not owner");

        address seller = listing.seller;
        listing.active = false;

        _transfer(seller, msg.sender, ticketId);
        payable(seller).transfer(listing.price);

        emit TicketSold(ticketId, msg.sender, listing.price);
    }

    function _tokenExists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }

    // Metadata
    function _setTokenURI(uint256 tokenId, string memory uri) internal {
        require(_tokenExists(tokenId), "Nonexistent token");
        _tokenURIs[tokenId] = uri;
    }

    function tokenURI(
        uint256 tokenId
    ) public view override returns (string memory) {
        require(_tokenExists(tokenId), "Nonexistent token");
        return _tokenURIs[tokenId];
    }

    // 署名驗證
    function getSigner(
        string memory message,
        bytes memory sig
    ) public pure returns (address) {
        bytes memory prefix = "\x19Ethereum Signed Message:\n";
        uint256 len = bytes(message).length;
        string memory lenStr = _uintToString(len);
        bytes memory fullPrefix = abi.encodePacked(prefix, lenStr);
        bytes32 ethSignedMessageHash = keccak256(
            abi.encodePacked(fullPrefix, message)
        );
        (bytes32 r, bytes32 s, uint8 v) = splitSignature(sig);
        return ecrecover(ethSignedMessageHash, v, r, s);
    }

    function splitSignature(
        bytes memory sig
    ) public pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(sig.length == 65, "Invalid signature length");
        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
    }

    function _uintToString(
        uint256 v
    ) internal pure returns (string memory str) {
        if (v == 0) return "0";
        uint256 j = v;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        j = v;
        while (j != 0) {
            bstr[--length] = bytes1(uint8(48 + (j % 10)));
            j /= 10;
        }
        str = string(bstr);
    }

    // Owner withdraw
    function withdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    // Override
    function supportsInterface(
        bytes4 interfaceId
    ) public view override(ERC721, ERC721Enumerable) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    function _increaseBalance(
        address account,
        uint128 amount
    ) internal override(ERC721, ERC721Enumerable) {
        super._increaseBalance(account, amount);
    }
}
