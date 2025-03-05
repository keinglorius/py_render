<?php
// Đường dẫn file input/output
$inputFile = "D:\\images\\layer1.png";
$outputEpsFile = "D:\\images\\black.eps";

// Kiểm tra hệ điều hành để thiết lập đường dẫn
if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
    $inkscapePath = "\"C:\\Program Files\\Inkscape\\bin\\inkscape.exe\"";
} else {
    $inkscapePath = "inkscape";
}

// Lệnh để chạy Inkscape
$command = $inkscapePath . " " . escapeshellarg($inputFile) . " --actions=" . escapeshellarg("select-all;object-to-path;trace-bitmap;export-filename:" . $outputEpsFile . ";export-do;file-close");

// Ghi lại thông tin về lệnh đang chạy
file_put_contents('log/command.log', $command . PHP_EOL, FILE_APPEND);

// Thực thi lệnh và bắt kết quả
exec($command . " 2>&1", $output, $return_var);

// Ghi lại output của lệnh và mã trả về
file_put_contents('log/output.log', implode("\n", $output) . PHP_EOL, FILE_APPEND);
file_put_contents('log/return_var.log', $return_var . PHP_EOL, FILE_APPEND);

// Kiểm tra kết quả thực thi lệnh
if ($return_var === 0) {
    if (file_exists($outputEpsFile)) {
        echo "File has been successfully converted to EPS.";
    } else {
        echo "Command executed successfully but output file not found.";
    }
} else {
    echo "Failed to convert file. Command output: " . implode("\n", $output);
}
