export async function uploadToPinata({
  file,
  fileName,
}: {
  file: Blob;
  fileName: string;
}): Promise<string> {
  const formData = new FormData();
  formData.append("file", file, fileName);

  const res = await fetch("https://api.pinata.cloud/pinning/pinFileToIPFS", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${import.meta.env.VITE_PINATA_JWT}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error?.reason || "Upload failed");
  }

  const data = await res.json();
  return `https://gateway.pinata.cloud/ipfs/${data.IpfsHash}`;
}
