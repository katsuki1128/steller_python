from flask import Flask, render_template, request, send_file
import openeo
import xarray
import rioxarray
import matplotlib.pyplot as plt
import os
from datetime import datetime
from tqdm import tqdm

# 非インタラクティブモードに設定
import matplotlib

matplotlib.use("Agg")

app = Flask(__name__)

# ======================
# CDESのバックエンドと接続
# ======================
connection = openeo.connect("openeo.dataspace.copernicus.eu")
# 接続の確認のため、SENTINEL2_L2のメタデータ詳細を取得し出力する
collection_metadata = connection.describe_collection("SENTINEL2_L2A")
# print(collection_metadata)
connection.authenticate_oidc()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    west = float(request.form["west"])
    south = float(request.form["south"])
    east = float(request.form["east"])
    north = float(request.form["north"])

    # datacubeの設定
    datacube = connection.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={
            "west": west,
            "south": south,
            "east": east,
            "north": north,
            "crs": "EPSG:4326",
        },
        temporal_extent=["2022-03-01", "2024-03-31"],
        bands=["B04", "B03", "B02", "SCL"],
        max_cloud_cover=20,
    )

    # ファイル名を指定
    # filename = "new.nc"
    # 現在の日時を取得してファイル名を生成
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"s2_{current_time}.nc"

    # ファイルの存在を確認して、存在しない場合のみダウンロード
    if not os.path.exists(filename):
        print(f"{filename} が存在しません。ダウンロードを開始します。")
        # download_with_progress(datacube, filename)
        datacube.download(filename)
    else:
        print(f"{filename} はすでに存在します。")

    # 保存したncデータをxarrayとして読み込む
    ds = xarray.open_dataset(filename)
    # print(ds)

    # 雲のカバー率を計算
    # cloud_cover = (ds["SCL"] == 3).mean(dim=["x", "y"])

    # 雲のカバー率が最も少ないタイムステップを選択
    # best_time_step = cloud_cover.argmin().item()

    # Scene Classification Layer (SCL)を取得した時系列で描画
    # ds["SCL"].plot.imshow(col="t")
    # plt.show()

    # xarrayデータセットを新しいデータアレイへ変換 (bands, t, x, y)
    # 新しい次元名をbandsとする（デフォルト名はvariable）
    # トゥルーカラー画像を生成 (最初のタイムステップを使用)
    # rgb_data = ds[["B04", "B03", "B02"]].isel(t=best_time_step).to_array(dim="bands")

    rgb_data = ds[["B04", "B03", "B02"]].isel(t=0).to_array(dim="bands")

    # デバッグ: rgb_dataの次元と座標を確認
    # print(rgb_data)

    output_image = f"static/rgb_{current_time}.png"
    # print(rgb_data)

    # staticディレクトリが存在しない場合は作成
    if not os.path.exists("static"):
        os.makedirs("static")

    # 手動でプロットを作成
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(rgb_data.transpose("y", "x", "bands").values / 10000.0)  # 正規化して表示
    plt.axis("off")
    plt.savefig(output_image, bbox_inches="tight", pad_inches=0)

    # # # 2024年2月10日から2024年3月21日までのデータをトゥルーカラー画像で描画
    # rgb_data.plot.imshow(vmin=0, vmax=2000, col="t", col_wrap=3, robust=True)
    # plt.show()
    # plt.savefig(output_image)
    plt.close(fig)

    # 使用した.ncファイルを削除
    os.remove(filename)

    # return render_template("index.html", image_url=output_image)
    # 画像のパスを返す
    return render_template("index.html", image_url=output_image, filename=filename)
    # return "プロセスが完了しました。トゥルーカラー画像が生成されました。"


# rds = rioxarray.open_rasterio("s2-amami.nc", decode_times=False, masked=True)
# rds["t"] = ds["t"]  # 時間データの上書き
# rds.isel(t=-1).rio.to_raster("sample_time_slice.tif")


if __name__ == "__main__":
    app.run(debug=True)
