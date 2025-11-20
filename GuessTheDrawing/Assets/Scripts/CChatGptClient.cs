using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json.Linq;
using UnityEngine.TextCore.Text;

public class ChatResponse
{
    public Choice[] choices;
}

public class Choice
{
    public Message message;
}

public class Message
{
    public string content;
}

public class CChatGptClient : MonoBehaviour
{
    [SerializeField] PromptGenerator promptGenerator;
    [SerializeField] int maxTokens = 300;
    
    //for debug
    [SerializeField] CTextBubble textBubble;

    private string apiKey = "";
    
    void Start()
    {
        string envPath = Application.dataPath + "/../.env";
        apiKey = EnvLoader.LoadEnv(envPath)["OPENAI_API_KEY"];
        //
    }

    public void Guess(byte[] pngBytes, Action<string> callback)
    {
        StartCoroutine(SendRequest(pngBytes, callback));
    }

    IEnumerator SendRequest(byte[] pngBytes, Action<string> callback = null)
    {
        // 1. 이미지 PNG → Base64
        string base64Image = Convert.ToBase64String(pngBytes);
        
        string systemMessage = promptGenerator.systemMessage;
        string prompt = promptGenerator.GeneratePrompt(0);

        // 2. JSON payload 구성
        string json = $@"
        {{
            ""model"": ""gpt-4.1-mini"",
            ""messages"": [
                {{
                    ""role"": ""system"",
                    ""content"": ""{systemMessage}""
                }},
                {{
                    ""role"": ""user"",
                    ""content"": [
                        {{ ""type"": ""text"", ""text"": ""{prompt}"" }},
                        {{
                            ""type"": ""image_url"",
                            ""image_url"": {{
                                ""url"": ""data:image/png;base64,{base64Image}""
                            }}
                        }}
                    ]
                }}
            ],
            ""max_tokens"": {maxTokens}
        }}";

        // 3. 요청 설정
        UnityWebRequest req = new UnityWebRequest("https://api.openai.com/v1/chat/completions", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
        req.uploadHandler = new UploadHandlerRaw(bodyRaw);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        req.SetRequestHeader("Authorization", $"Bearer {apiKey}");  // ← 여기에 API 키 입력
        
        // 4. 요청 보내기
        yield return req.SendWebRequest();
        
        // 5. 응답 처리
        if (req.result == UnityWebRequest.Result.Success)
        {
            callback?.Invoke(GetContentFromResponse(req.downloadHandler.text));
        }
        else
        {
            Debug.LogError("Error:\n" + req.error);
            textBubble.TextBubbleSetText("Error:\n" + req.error);
        }
        
    }
    
    string GetContentFromResponse(string json)
    {
        JObject root = JObject.Parse(json);
        string content = root["choices"]?[0]?["message"]?["content"]?.ToString();

        Debug.Log("응답: " + content);
        return content;
    }
    
}


