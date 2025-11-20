using System;
using System.Text;
using UnityEngine;
using DG.Tweening;
using Unity.VisualScripting;
using UnityEngine.UI;

public class CTextBubble : MonoBehaviour
{
    [SerializeField] GameObject bubble;
    [SerializeField] CTextUIElement text;
    [SerializeField] int charsPerLineKor = 30;
    [SerializeField] int charsPerLineEng = 50;

    public float animationDuration = 0.3f;

    private bool isActive = false;

    private void Awake()
    {
        isActive = false;
        bubble.SetActive(false);
        bubble.transform.localScale = Vector3.zero;
    }

    public void ShowTextBubble()
    {
        if (isActive) return;
        isActive = true;
        bubble.SetActive(true);
        bubble.transform.localScale = Vector3.zero;
        bubble.transform.DOScale(Vector3.one, animationDuration).SetEase(Ease.OutBack);
    }

    public void HideTextBubble()
    {
        if (!isActive) return;
        isActive = false;
        bubble.transform.DOScale(Vector3.zero, animationDuration)
            .SetEase(Ease.OutSine)
            .OnComplete(() => bubble.SetActive(false));
    }
    public void TextBubbleSetText(string t, bool format = true)
    {
        if (format)
        {
            t = InsertLineBreaks(t, charsPerLineKor, true);
        }
        if (!isActive)
        {
            ShowTextBubble();
            text.SetTextTween(t, animationDuration);
        }
        else text.SetTextTween(t);
    }

    //mode 0: 단순 n글자마다 줄바꿈, 1: 단어 단위 줄바꿈
    private static string InsertLineBreaks(string source, int n, bool mode = false)
    {
        if (string.IsNullOrEmpty(source) || n <= 0) return source;
        var sb = new StringBuilder(source.Length + source.Length / n + 8);
        if (mode == false)
        {
            for (int i = 0; i < source.Length; i++)
            {
                sb.Append(source[i]);
                if ((i + 1) % n == 0 && (i + 1) != source.Length)
                    sb.Append('\n');
            }
        }
        else if (mode == true)
        {
            int charCount = 0;
            string[] words = source.Split(' ');
            for (int i = 0; i < words.Length; i++)
            {
                string word = words[i];
                if (charCount + word.Length > n)
                {
                    if (i != 0)
                        sb.Append('\n');
                    charCount = 0;
                }
                else if (i != 0)
                {
                    sb.Append(' ');
                    charCount++;
                }
                sb.Append(word);
                charCount += word.Length;
            }
        }
        return sb.ToString();
    }
}