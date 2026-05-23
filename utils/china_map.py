"""
中国省级地图（vanilla ECharts + 本地打包 GeoJSON）
================================================
GeoJSON 文件 data/china_geo.json 已随项目打包，不依赖外网 CDN。
省份名使用全称（北京市/新疆维吾尔自治区），数据 name 必须匹配。
"""

from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import streamlit.components.v1 as components


# GeoJSON 文件路径（项目根目录 / data / china_geo.json）
_GEO_JSON_PATH = Path(__file__).resolve().parents[1] / "data" / "china_geo.json"


def render_china_depression_map(df: pd.DataFrame,
                                province_col: str = "province",
                                value_col: str = "rate",
                                height: int = 460) -> None:
    """渲染交互式中国省级抑郁检出率热力图（深色霓虹）。
    df[province_col] 必须使用与 GeoJSON 一致的全称（例如 "新疆维吾尔自治区"）。
    """
    items = []
    for _, row in df.iterrows():
        items.append({"name": row[province_col], "value": float(row[value_col])})
    data_json = json.dumps(items, ensure_ascii=False)

    vmin = round(min(d["value"] for d in items) - 0.3, 1)
    vmax = round(max(d["value"] for d in items) + 0.3, 1)

    # 读取本地 GeoJSON（在 Streamlit Cloud 上也能稳定加载，不依赖外网）
    try:
        geo_json_text = _GEO_JSON_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        # 文件丢失时降级到 CDN（本地开发兜底）
        geo_json_text = "null"

    # 用占位符避开 f-string 对 { } 的解析问题
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{margin:0; padding:0; background:transparent;
        font-family: PingFang SC, "Microsoft YaHei", Arial;}}
  #map {{width:100%; height:{height}px; background:transparent;}}
  #status {{
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    color: #5BC8FF; font-size: 13px; letter-spacing: 1px;
  }}
</style>
</head>
<body>
  <div id="map"></div>
  <div id="status">⏳ 正在加载中国地图…</div>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
  <script>
    const data = {data_json};
    const chart = echarts.init(document.getElementById('map'),
                                'dark', {{renderer: 'canvas'}});

    // GeoJSON 已嵌入页面（来自本地 data/china_geo.json），不再依赖外网 fetch
    const geoJson = __CHINA_GEOJSON__;

    function renderMap() {{
      if (!geoJson) {{
        document.getElementById('status').innerText = '❌ GeoJSON 数据缺失';
        return;
      }}
      echarts.registerMap('china', geoJson);
      document.getElementById('status').style.display = 'none';
      chart.setOption({{
        backgroundColor: 'transparent',
        title: {{
          text: '中国成人抑郁检出率分布（%）',
          subtext: '数据范围参考 Lu et al. 2021 Lancet Psychiatry (4.5%-9.5%)',
          left: 'left', top: 8,
          textStyle: {{color: '#5BC8FF', fontSize: 13, fontWeight: 'bold'}},
          subtextStyle: {{color: '#9CA3AF', fontSize: 10}},
          itemGap: 4,
        }},
        tooltip: {{
          trigger: 'item',
          formatter: function(p) {{
            if (p.value === undefined || p.value === null || isNaN(p.value)) {{
              return '<b>' + p.name + '</b><br/>暂无数据';
            }}
            return '<b>' + p.name + '</b><br/>抑郁检出率 ' + p.value.toFixed(2) + '%';
          }},
          backgroundColor: 'rgba(10,11,30,0.95)',
          borderColor: '#5BC8FF', borderWidth: 1,
          textStyle: {{color: '#E8F0FF', fontSize: 12}},
          extraCssText: 'box-shadow: 0 0 14px rgba(91,200,255,0.4);',
        }},
        visualMap: {{
          min: {vmin}, max: {vmax},
          left: '3%', bottom: '8%',
          calculable: true,
          inRange: {{
            color: ['#1E3A8A', '#3B82F6', '#8B5CF6', '#EC4899', '#EF4444']
          }},
          textStyle: {{color: '#E8F0FF', fontSize: 10}},
          text: ['高 (%)', '低 (%)'],
          itemHeight: 100, itemWidth: 14,
        }},
        series: [{{
          name: '抑郁检出率',
          type: 'map',
          map: 'china',
          roam: false,
          zoom: 1.05,
          top: '22%',
          bottom: '8%',
          label: {{show: false}},
          emphasis: {{
            label: {{
              show: true,
              color: '#FFFFFF',
              fontSize: 11,
              fontWeight: 'bold',
              textBorderColor: '#0A0B1E',
              textBorderWidth: 2,
            }},
            itemStyle: {{
              areaColor: '#5BC8FF',
              borderColor: '#FFFFFF', borderWidth: 1.5,
              shadowColor: 'rgba(91,200,255,0.6)',
              shadowBlur: 18,
            }},
          }},
          itemStyle: {{
            borderColor: 'rgba(91,200,255,0.5)',
            borderWidth: 0.6,
            areaColor: 'rgba(40,42,80,0.6)',
          }},
          data: data,
        }}],
      }});
    }}

    renderMap();
    window.addEventListener('resize', () => chart.resize());
  </script>
</body>
</html>
    """
    # 把占位符替换为真正的 GeoJSON 文本（避免 f-string 处理巨量花括号）
    html = html.replace("__CHINA_GEOJSON__", geo_json_text)
    components.html(html, height=height + 20, scrolling=False)
