using System;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

public class CPaint : MonoBehaviour {
    
    private int width;
    private int height;
    private RectTransform rt;
    // image: 그림판 UI 이미지
    private RawImage image;
    // texture: 그림판에 사용할 Texture2D
    private Texture2D texture;
    private Camera cam;
    
    public CBrush brush;

    private Vector2Int? prevCoord = null;
    
    private static string SavePath => Path.Combine(Application.persistentDataPath, "Drawings");

    private void Awake()
    {
        rt = GetComponent<RectTransform>();
        width = (int)rt.rect.width;
        height = (int)rt.rect.height;
        
        ResetCanvas();
    }

    void ResetTexture(Texture2D texture)
    {
        for (int x = 0; x < texture.width; x++) {
            for (int y = 0; y < texture.height; y++) {
                texture.SetPixel(x, y, Color.white);
            }
        }
        texture.Apply();
    }

    void Update() {
        if (Input.GetMouseButton(0)) {
            Vector2 mousePos = Input.mousePosition;

            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                image.rectTransform, mousePos, cam, out Vector2 localPoint);

            Vector2Int currCoord = ConvertToTextureCoord(localPoint);

            if (prevCoord.HasValue) {
                Vector2Int prev = prevCoord.Value;
                DrawLine(prev, currCoord);
            }

            prevCoord = currCoord;
        } else {
            prevCoord = null;
        }
    }
    
    void DrawAt(Vector2Int coord) {
        
        int brushSize = brush.size;
        Color brushColor = brush.color;

        for (int x = -brushSize; x < brushSize; x++) {
            for (int y = -brushSize; y < brushSize; y++) {
                int px = coord.x + x;
                int py = coord.y + y;

                if (px < 0 || py < 0 || px >= texture.width || py >= texture.height)
                    continue;

                float distance = Mathf.Sqrt(x * x + y * y);
                if (distance <= brushSize)
                {
                    float a = brush.antiAliasing.Evaluate(distance / (float)brushSize);
                    Color baseColor = texture.GetPixel(px, py);
                    Color blended = Color.Lerp(baseColor, brushColor, a);
                    texture.SetPixel(px, py, blended);
                }
            }
        }

        texture.Apply();
    }

    void DrawLine(Vector2Int from, Vector2Int to) {
        int steps = Mathf.CeilToInt(Vector2Int.Distance(from, to));
        for (int i = 0; i <= steps; i++) {
            float t = i / (float)steps;
            Vector2 lerped = Vector2.Lerp(from, to, t);
            DrawAt(Vector2Int.RoundToInt(lerped));
        }
    }
    
    // localPoint: RawImage의 로컬 좌표 (RectTransform 기준)
    Vector2Int ConvertToTextureCoord(Vector2 localPoint)
    {
        // RectTransform 정보 가져오기
        Rect rect = image.rectTransform.rect;

        // 로컬 좌표를 [0, 1] 범위의 비율로 변환
        float normalizedX = (localPoint.x - rect.x) / rect.width;
        float normalizedY = (localPoint.y - rect.y) / rect.height;

        // Texture 좌표로 변환
        int texX = Mathf.FloorToInt(normalizedX * texture.width);
        int texY = Mathf.FloorToInt(normalizedY * texture.height);

        return new Vector2Int(texX, texY);
    }

    [ContextMenu( "Convert Drawing" )]
    public bool ConvertDrawing(out byte[] pngData)
    {
        pngData = texture.EncodeToPNG();
        // 저장
        try
        {
            //current time + Drawing + .png
            string imgName = DateTime.Now.ToString("yyyyMMdd_HHmmss") + "_Drawing.png";
            string filePath = Path.Combine(SavePath, imgName);
            if (!Directory.Exists(SavePath)) Directory.CreateDirectory(SavePath);
            File.WriteAllBytes(filePath, pngData);
            Debug.Log("Drawing saved to: " + filePath);
            return true;
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            return false;
        }
        
    }
    
    public void ResetCanvas()
    {
        // 시작 시 빈 Texture2D를 만들고 RawImage에 적용
        texture = new Texture2D(width, height);
        ResetTexture(texture);
        image = GetComponent<RawImage>();
        image.texture = texture;
    }
}

