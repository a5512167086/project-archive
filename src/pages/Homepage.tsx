import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSearchParams } from "react-router";
import liff from "@line/liff";
import { fetchCommandData } from "@/lib/helpers";

export default function CommandGenerator() {
  const [commands, setCommands] = useState<
    { command_keyword: string; type: string; status: boolean }[]
  >([]);
  const [selectedCommand, setSelectedCommand] = useState("");
  const [textInput, setTextInput] = useState("");

  const [searchParams] = useSearchParams();
  const botUUID = searchParams.get("bot_uuid");

  useEffect(() => {
    const fetchData = async () => {
      if (botUUID) {
        try {
          const commandData = await fetchCommandData(botUUID);
          setCommands(commandData);
        } catch (error) {
          console.error("獲取命令數據時發生錯誤:", error);
        }
      }
    };

    fetchData();
  }, [botUUID]);

  const handleCommandChange = (value: string) => {
    setSelectedCommand(value);
    setTextInput("");
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTextInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (liff?.isInClient()) {
      liff
        ?.sendMessages([
          {
            type: "text",
            text: `${selectedCommand} ${textInput}`,
          },
        ])
        .finally(() => {
          liff.closeWindow();
        });
    }
  };

  return (
    <div className="flex min-h-screen relative flex-col items-center justify-center p-4 border-0">
      <Card className="w-[350px]">
        <CardHeader>
          <CardTitle>選擇指令</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="grid w-full items-center gap-4">
              <div className="flex flex-col space-y-1.5">
                <Label htmlFor="command">指令</Label>
                <Select onValueChange={handleCommandChange}>
                  <SelectTrigger id="command">
                    <SelectValue placeholder="選擇一個指令" />
                  </SelectTrigger>
                  <SelectContent position="popper">
                    {commands.map((command) => (
                      <SelectItem
                        key={command.command_keyword}
                        value={`!${command.command_keyword}`}
                      >
                        {command.type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedCommand === "!search" && (
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="textInput">輸入要查詢的內容</Label>
                  <Input
                    id="textInput"
                    value={textInput}
                    onChange={handleTextChange}
                    placeholder="請輸入文字"
                  />
                </div>
              )}
            </div>
          </form>
        </CardContent>
        <CardFooter>
          <Button onClick={handleSubmit}>提交</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
