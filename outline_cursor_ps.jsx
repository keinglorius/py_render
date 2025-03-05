// Script để vẽ outline dạng cursor theo đối tượng trong Photoshop

// Lấy tham số input và output từ đối số dòng lệnh
var inputFile = decodeURIComponent(arguments[0]);
var outputFile = decodeURIComponent(arguments[1]);

// Mở file PNG
var doc = open(new File(inputFile));

// Vẽ outline dạng cursor
var path = doc.pathItems.add("CursorOutline", [
    [10, 10],
    [50, 10],
    [50, 50],
    [10, 50],
    [10, 10]
]);

// Tạo hiệu ứng bo tròn
var strokeOptions = new StrokeOptions();
strokeOptions.strokeWidth = 2;
strokeOptions.strokeColor = new SolidColor();
strokeOptions.strokeColor.rgb.red = 255;
strokeOptions.strokeColor.rgb.green = 0;
strokeOptions.strokeColor.rgb.blue = 0;
strokeOptions.strokeBrush = app.brushes.getByName("Round Brush");
path.stroke(strokeOptions);

// Lưu file
if (outputFile.toLowerCase().endsWith(".ps")) {
    var psOptions = new PhotoshopSaveOptions();
    doc.saveAs(new File(outputFile), psOptions);
} else if (outputFile.toLowerCase().endsWith(".eps")) {
    var epsOptions = new EPSSaveOptions();
    doc.saveAs(new File(outputFile), epsOptions);
}

// Đóng tài liệu mà không lưu thay đổi
doc.close(SaveOptions.DONOTSAVECHANGES);