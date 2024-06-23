import openeo
import xarray
import rioxarray
import matplotlib.pyplot as plt
import os

# CDESのバックエンドと接続
connection = openeo.connect("openeo.dataspace.copernicus.eu")

# 接続の確認のため、SENTINEL2_L2のメタデータ詳細を取得し出力する
collection_metadata = connection.describe_collection("SENTINEL2_L2A")
# print(collection_metadata)

connection.authenticate_oidc()

# 沖縄の北部を検索対象に設定
datacube = connection.load_collection(
    "SENTINEL2_L2A",
    spatial_extent={
        "west": 129.35,
        "south": 28.35,
        "east": 129.45,
        "north": 28.43,
        "crs": "EPSG:4326",
    },
    temporal_extent=["2024-03-01", "2024-03-31"],
    bands=["B04", "B03", "B02", "SCL"],
    max_cloud_cover=85,
)

# ファイル名を指定
filename = "s2-amami.nc"

# ファイルの存在を確認して、存在しない場合のみダウンロード
if not os.path.exists(filename):
    print(f"{filename} が存在しません。ダウンロードを開始します。")
    datacube.download(filename)
else:
    print(f"{filename} はすでに存在します。")

# 保存したncデータをxarrayとして読み込む
ds = xarray.open_dataset("s2-amami.nc")
# print(ds)

# Scene Classification Layer (SCL)を取得した時系列で描画
# ds["SCL"].plot.imshow(col="t")
# plt.show()

# xarrayデータセットを新しいデータアレイへ変換 (bands, t, x, y)
# 新しい次元名をbandsとする（デフォルト名はvariable）
# rgb_data = ds[["B04", "B03", "B02"]].to_array(dim="bands")
# print(rgb_data)

# # # 2024年2月10日から2024年3月21日までのデータをトゥルーカラー画像で描画
# rgb_data.plot.imshow(vmin=0, vmax=2000, col="t", col_wrap=3, robust=True)
# plt.show()

rds = rioxarray.open_rasterio("s2-amami.nc", decode_times=False, masked=True)
rds["t"] = ds["t"]  # 時間データの上書き
rds.isel(t=-1).rio.to_raster("sample_time_slice.tif")
