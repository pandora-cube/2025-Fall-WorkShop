using System.Collections.Generic;
using UnityEngine;

[ CreateAssetMenu(fileName = "PromptGenerator", menuName = "Scriptable Objects/PromptGenerator")]
public class PromptGenerator : ScriptableObject {
    public string systemMessage;
    public List<string> prompts;
    
    public string GeneratePrompt(int index)
    {
        return prompts[index];
    }
}
