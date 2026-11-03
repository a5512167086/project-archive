import { useEffect, createContext, useContext, useState } from "react";
import { BrowserProvider } from "ethers";

interface WalletContextProps {
  account: string;
  signer: any;
  connectWallet: () => Promise<void>;
}

const WalletContext = createContext<WalletContextProps>({
  account: "",
  signer: null,
  connectWallet: async () => {},
});

export const WalletProvider = ({ children }: { children: React.ReactNode }) => {
  const [account, setAccount] = useState("");
  const [signer, setSigner] = useState<any>(null);

  const connectWallet = async () => {
    if (!window.ethereum) return alert("請先安裝 MetaMask");

    const provider = new BrowserProvider(window.ethereum);
    const signer = await provider.getSigner();
    const address = await signer.getAddress();
    const network = await signer.provider.getNetwork();
    console.log("🧭 Connected to network:", network.name, network.chainId);
    console.log(signer, address, network);

    setAccount(address);
    setSigner(signer);
  };

  useEffect(() => {
    if (!window.ethereum) return;

    // 自動偵測已授權的帳號
    window.ethereum
      .request({ method: "eth_accounts" })
      .then(async (accounts: string[]) => {
        if (accounts.length > 0) {
          const provider = new BrowserProvider(window.ethereum);
          const signer = await provider.getSigner();
          const address = await signer.getAddress();
          setAccount(address);
          setSigner(signer);
        }
      });

    // 監聽帳號切換
    const handleAccountsChanged = async (accounts: string[]) => {
      if (accounts.length === 0) {
        setAccount("");
        setSigner(null);
      } else {
        const provider = new BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const address = await signer.getAddress();
        setAccount(address);
        setSigner(signer);
      }
    };

    window.ethereum.on("accountsChanged", handleAccountsChanged);

    return () => {
      window.ethereum.removeListener("accountsChanged", handleAccountsChanged);
    };
  }, []);

  return (
    <WalletContext.Provider value={{ account, signer, connectWallet }}>
      {children}
    </WalletContext.Provider>
  );
};

export const useWallet = () => useContext(WalletContext);
