using System.IO;
using System.Collections.Generic;
using UnityEngine;

public static class EnvLoader
{
    public static Dictionary<string, string> LoadEnv(string path)
    {
        var result = new Dictionary<string, string>();

        if (!File.Exists(path)) {
            Debug.LogError(".env 파일을 찾을 수 없습니다: " + path);
            return result;
        }

        foreach (var line in File.ReadAllLines(path)) {
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#")) continue;

            var split = line.Split('=', 2);
            if (split.Length == 2) {
                result[split[0].Trim()] = split[1].Trim();
            }
        }

        return result;
    }
}