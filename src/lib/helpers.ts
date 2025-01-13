import axios from "axios";

export const fetchCommandData = async (botClassId: string) => {
  try {
    const response = await axios.get(
      `https://easybot.wke.csie.ncnu.edu.tw/commandapi/command/${botClassId}`
    );
    return response.data;
  } catch (error) {
    console.error("獲取命令數據時發生錯誤:", error);
    throw error;
  }
};
