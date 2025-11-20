using UnityEngine;

[CreateAssetMenu(fileName = "CBrush", menuName = "Scriptable Objects/CBrush")]
public class CBrush : ScriptableObject {
    public int size;
    public Color color;
    public AnimationCurve antiAliasing;
}
