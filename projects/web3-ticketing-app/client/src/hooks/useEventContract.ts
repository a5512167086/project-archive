import { Contract } from "ethers";
import { useMemo } from "react";
import { useWallet } from "@/context/WalletContext";
import abi from "@/abi/EventTicketing.json";

const CONTRACT_ADDRESS = "0x9f97a72C5623A6Ca05bd0dA56c1Eb9Cb7e0A6c1f";

export function useEventContract() {
  const { signer } = useWallet();

  return useMemo(() => {
    if (!signer) return null;
    return new Contract(CONTRACT_ADDRESS, abi, signer);
  }, [signer]);
}
