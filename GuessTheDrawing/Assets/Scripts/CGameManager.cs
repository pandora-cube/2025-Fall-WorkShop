using System;
using System.Collections.Generic;
using UnityEngine;
using Random = UnityEngine.Random;

public class CGameManager : Singleton<CGameManager> {
    [SerializeField] private CPaint paint;
    [SerializeField] private CChatGptClient chatGptClient;
    [SerializeField] CCharacter character;

    [SerializeField] private List<string> texts;
    [SerializeField] private List<string> finishTexts;
    [SerializeField] private CTextUIElement timerText;

    private Timer timer = new Timer();

    private void Start()
    {
        timer.Unset();
    }

    public void EndDrawing()
    {
        if (!paint.ConvertDrawing(out var file)) return;
        chatGptClient.Guess(file, OnResponse);
        character.SetSpeachBubble(texts[Random.Range(0, texts.Count)]);
        timer.Unset();
    }

    public void OnResponse(string response)
    {
        character.SetSpeachBubble(response);
    }

    public void SetTimer(float time = 30f)
    {
        timer.Set(time);
    }

    public void AddTimer(float time = 10f)
    {
        if (timer.IsSet)
            timer.Add(time);
    }

    public void ResetDrawing()
    {
        character.HideSpeachBubble();
        paint.ResetCanvas();
        timer.Unset();
    }

    private void Update()
    {
        if (timer.Remaining <= 0f && timer.IsSet)
        {
            timer.Unset();
            character.SetSpeachBubble(finishTexts[Random.Range(0, finishTexts.Count)]);
        }
        if (timer.IsSet)
            timerText.SetText(Mathf.CeilToInt(timer.Remaining).ToString());
        else
            timerText.SetText("");
    }
}
