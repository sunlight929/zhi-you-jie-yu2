"""
中国省级地图（vanilla ECharts + datav.aliyun GeoJSON 嵌入）
========================================================
GeoJSON 用的是省份全称（北京市/新疆维吾尔自治区），数据 name 必须匹配。
"""

from __future__ import annotations
import json
import pandas as pd
import streamlit.components.v1 as components


def render_china_depression_map(df: pd.DataFrame,
                                province_col: str = "province",
                                value_col: str = "rate",
                                height: int = 460) -> None:
    """渲染交互式中国省级抑郁检出率热力图（深色霓虹）。
    df[province_col] 必须使用与 GeoJSON 一致的全称（例如 "新疆维吾尔自治区"）。
    """
    items = []
    for _, row in df.iterrows():
        # 直接使用全称，与 GeoJSON properties.name 完全匹配
        items.append({"name": row[province_col], "value": float(row[value_col])})
    data_json = json.dumps(items, ensure_ascii=False)

    vmin = round(min(d["value"] for d in items) - 0.3, 1)
    vmax = round(max(d["value"] for d in items) + 0.3, 1)

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

    fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
      .then(r => r.json())
      .then(geo => {{
        echarts.registerMap('china', geo);
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
            // 默认不显示标签，避免名字互相重叠
            label: {{show: false}},
            // hover 时才显示
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
      }})
      .catch(err => {{
        document.getElementById('status').innerText =
          '❌ 地图加载失败：' + err.message;
      }});

    window.addEventListener('resize', () => chart.resize());
  </script>
</body>
</html>
    """
    components.html(html, height=height + 20, scrolling=False)
