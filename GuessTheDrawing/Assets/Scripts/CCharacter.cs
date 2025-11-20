using TMPro;
using UnityEditor;
using UnityEngine;

public class CCharacter : MonoBehaviour {
    [SerializeField] private CTextBubble speachBubble;
    
    public void SetSpeachBubble(string text)
    {
        speachBubble.TextBubbleSetText(text);
    }
    
    public void HideSpeachBubble()
    {
        speachBubble.HideTextBubble();
    }

    public void Adveertise()
    {
        speachBubble.TextBubbleSetText("DiceInYou 출시 만관부");
    }
}
