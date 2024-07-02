import cv2
import numpy as np
import requests

#----------------code hoan chinh-----------------------#

# Pretreatment: Chuyển ảnh đầu vào thành ảnh xám và thực hiện một loạt các bước tiền xử lý như loại bỏ nhiễu, làm đồng nhất lược đồ màu, và áp dụng ngưỡng nhị phân để phân đoạn ảnh.

# contours_detect: Tìm các đường viền trong ảnh đã được xử lý trước.

# find_number: Xác định vị trí của các ký tự trên biển số xe, cắt từng ký tự ra và sử dụng một mô hình SVM đã được huấn luyện trước để nhận diện ký tự. Ký tự nhận diện được sẽ được vẽ lên ảnh và trả về dưới dạng một chuỗi.

# findLP_img: Hàm này tìm và nhận diện vùng chứa biển số xe trong ảnh.

# Read_LP_from_photo: Kết hợp các chức năng trên để đọc biển số từ một luồng video từ camera IP.



#khởi tạo kích thước của kí tự trên biển số
digit_w =30
digit_h =60

#Ba hàm này đưa về giá trị cho mỗi cột (x, y, ký tự) nhằm để vào hàm sort(key=) để sắp xếp
def takeSecond(elem):
    return elem[1]

def takeFirst(elem):
    return elem[0]

def takeChar(elem):
    return elem[2]

def Pretreatment(imgLP):
    grayImg = cv2.cvtColor(imgLP, cv2.COLOR_BGR2GRAY)
    noise_removal = cv2.bilateralFilter(grayImg,9,75,75)
    #equal_histogram = cv2.equalizeHist(noise_removal)
    _, binImg = cv2.threshold(grayImg, 100, 255, cv2.THRESH_BINARY_INV+ cv2.THRESH_OTSU)
    kerel3 = cv2.getStructuringElement(cv2.MORPH_RECT,(1,4))
    binImg = cv2.morphologyEx(binImg,cv2.MORPH_DILATE,kerel3)
    return binImg

def contours_detect(binImg):
    #tìm contour
    cnts, _ = cv2.findContours(binImg, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    #tạo ảnh tạm để giữ ảnh gốc k bị edit
    return cnts

def draw_rects_on_img(img, cnts):
    imgtemp=img.copy()
    cv2.drawContours(imgtemp,cnts,-1,(0,120,0),1)
    return imgtemp
    #cv2.imshow('Number on License plate ',imgtemp)
    # print (cnts);

#khởi tạo 
plate_number=''
coorarr=[]
firstrow=[]
lastrow=[]
model_svm =cv2.ml.SVM_load('svm.xml')
plate_cascade = cv2.CascadeClassifier("./cascade2.xml")


def find_number(cnts,binImg,imgtemp):
    count=0
    global plate_number
    global coorarr
    global firstrow
    global lastrow
    (himg,wimg,chanel)=imgtemp.shape
    if(wimg/himg >2):
        hf=himg*0.6
        hl=himg*0.8
    else:
        hf=0.3*himg
        hl=0.4*himg
    plate_number = ''
    for c in (cnts):
        x,y,w,h=cv2.boundingRect(c)
        cv2.rectangle(imgtemp, (x, y), (x + w, y + h), (0, 255, 0), 1)
        if h/w >1.5 and h/w <4 and h>=hf or cv2.contourArea(c)>4600 and h<= hl: 
            #4500 là kích thước tối thiểu của diện tích contour đảm bảo cho các contour "rác" không nhận diện
            #7000 là kích thước tối đa của contour số đảm bảo không nhận diện contour "rác" có cỡ lớn, chủ yếu đến từ viền biển số
            #Đóng khung cho kí tự
            cv2.rectangle(imgtemp, (x, y), (x + w, y + h), (0, 0, 255),2)
            #crop thành những số riêng lẻ
            crop=imgtemp[y:y+h, x:x+w]
            #dùng để ghi vào thư mục number
            count+=1
            cv2.imwrite('./number/number%d.jpg'% count,crop)

            #tách số và predict
            binImgtemp=binImg
            curr_num=binImgtemp[y:y+h, x:x+w]
            #đầu tiên là resize lại cho nó cùng kích thước nhau cũng như bang kích thước khi train
            curr_num=cv2.resize(curr_num,dsize=(digit_w,digit_h))
            _, curr_num=cv2.threshold(curr_num,30,255,cv2.THRESH_BINARY)
            #chuyển thành np để tí xài tạo thàn h mảng numpy
            curr_num= np.array(curr_num,dtype=np.float32)
            #reshape lại nha ae tự sắp xếp thành hàng ngang thì phải
            curr_num=curr_num.reshape(-1,digit_w*digit_h)

            #train
            result=model_svm.predict(curr_num)[-1]
            result= int(result[0,0])

            if result<=9: 
                result= str(result)
            else:
                result=chr(result)
            # plate_number +=result+' '
            #này dùng viết lên màn hình thui ae
            coorarr.append((x,y,result))
            cv2.putText(imgtemp,result,(x-50,y+50),cv2.FONT_HERSHEY_COMPLEX,3,(0, 255, 0), 2, cv2.LINE_AA)
    #sắp xếp theo y, nhằm lấy hàng đầu tiên với y thấp nhất
    coorarr.sort(key=takeSecond)
    #Lấy ra 4 giá trị đầu tiên có y thấp nhất, nhằm đưa về hàng đầu
    firstrow = coorarr[:4]
    #Sắp xếp lại hàng đầu từ trái qua phải
    firstrow.sort(key=takeFirst)
    #tương tự với hàng sau
    lastrow = coorarr[4:]
    lastrow.sort(key=takeFirst)
    #Đưa từng hàng vào 
    for x, y, c in firstrow:
        plate_number+=c
    for x, y, c in lastrow:
        plate_number+=c
    return imgtemp, plate_number



def detect(img):
    (himg,wimg,chanel)=img.shape
    if(wimg/himg >2):
        img=cv2.resize(img,dsize=(1000,200))
    else:
        img=cv2.resize(img,dsize=(800,500))

    binImg=Pretreatment(img)
    cnts=contours_detect(binImg)
    imgtemp=draw_rects_on_img(img,cnts)
    _, sort_number = find_number(cnts,binImg,imgtemp)
    # sort_number = sortNumber();
    # print('bien so xe: ',sort_number)
    plate_number=''
    coorarr.clear()
    return sort_number

def findLP_img(OriImg): 
    #nhận diện biển trong img
    plates = plate_cascade.detectMultiScale(OriImg, 1.1, 3)
    #Tạo ảnh trước khi cắt
    img = OriImg
    #in vùng chứa biển số và cắt
    for (x,y,w,h) in plates:
        cv2.rectangle(OriImg,(x,y),(x+w,y+h),(255,0,0),1)
        img = OriImg[y:y+h, x:x+w]
        plate_num = detect(img)
        cv2.putText(OriImg, plate_num, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)
    #cv2.imshow("Original image", OriImg)
    # cv2.imshow("crop",img)
    return img


def Read_LP_from_photo(ipCamAdd, portNum):
    #Tìm biển số
    img_res = requests.get("http://192.168.45.97:8080/photo.jpg")
    img_arr = np.array(bytearray(img_res.content), dtype = np.uint8)
    OriImg = cv2.imdecode(img_arr,-1)
    img=findLP_img(OriImg)
    #resize lại hình
    (himg,wimg,chanel)=img.shape
    if(wimg/himg >2):
        img=cv2.resize(img,dsize=(1000,200))
    else:
        img=cv2.resize(img,dsize=(800,500))
    # cv2.imshow('Image',img)

    binImg=Pretreatment(img)
    cnts=contours_detect(binImg)
    imgtemp=draw_rects_on_img(img,cnts)
    imgtemp, sort_number=find_number(cnts,binImg,imgtemp)

    cv2.imshow('binary',binImg)
    cv2.imshow('result',imgtemp)
 
    #print('bien so xe: ',sort_number)

    cv2.waitKey()

    cv2.destroyAllWindows()
    return sort_number


if __name__ == "__main__":
       camIP = "192.168.45.97"
       port = "8080"
       Data = Read_LP_from_photo(camIP, port)
       print(Data)