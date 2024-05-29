//登入後按member icon顯示的東西
/*window.addEventListener("beforeunload", function () {
  navigator.sendBeacon("/logout");
});*/
document.addEventListener("DOMContentLoaded", function () {
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl, {
      html: true, // Enable HTML content in the popover
    });
  });
});
//-----------------------------------------------------------
//"顯示總價"
function calculateAndAppendTotalPrice(offcanvasBody) {
  // 从本地存储中获取购物车数据
  let cartData = localStorage.getItem("cartData");

  // 如果购物车数据不存在，则初始化为空数组
  if (!cartData) {
    cartData = [];
  } else {
    // 尝试将 cartData 转换为数组
    try {
      cartData = JSON.parse(cartData);
    } catch (e) {
      // 如果转换失败，初始化为空数组
      cartData = [];
    }
  }

  // 初始化总价为 0
  let totalCost = 0;

  // 遍历购物车数据计算总价
  for (const item of cartData) {
    // 确保 item.Price 是一个数字类型
    const price = parseFloat(item.Price);
    if (!isNaN(price)) {
      totalCost += price;
    }
  }

  // 如果 cartData 为空数组，直接返回，不执行添加操作
  if (cartData.length === 0) {
    return;
  }

  // 查找并删除 offcanvas-body 中包含 "總價:" 的 div 元素
  const divs = offcanvasBody.getElementsByTagName("div");
  for (let i = 0; i < divs.length; i++) {
    const div = divs[i];
    if (div.textContent.includes("總價:")) {
      offcanvasBody.removeChild(div);
      break; // 只删除第一个匹配项
    }
  }

  // 创建一个新的 div 元素显示总价
  const totalCostDiv = document.createElement("div");
  totalCostDiv.textContent = `總價: $${totalCost}`;

  // 将总价 div 添加到 offcanvas-body 元素中
  offcanvasBody.appendChild(totalCostDiv);
}
//"顯示總價" END
//------------------------------------------------------------------
//loadCartData()
function loadCartData() {
  const cartData = JSON.parse(localStorage.getItem("cartData"));
  const offcanvasBody = document.getElementById("offcanvas-body");
  const buyNowButton = document.querySelector(".inCart-buyNow");

  // 清空 offcanvas-body 的内容
  offcanvasBody.innerHTML = "";

  if (cartData && cartData.length > 0) {
    // 遍历 cartData 数组
    cartData.forEach((product) => {
      // 创建一个新的 div 元素
      const productInfoDiv = document.createElement("div");

      // 设置 div 的文本内容为商品名称和数量
      productInfoDiv.textContent = `${product.productName} * ${
        product.quantity
      } ${" ".repeat(5)}$${product.Price}`;

      // 将新的 div 元素添加到 offcanvas-body 元素中
      offcanvasBody.appendChild(productInfoDiv);
    });

    // 显示结账按钮
    buyNowButton.style.display = "block";
  } else {
    // 如果 cartData 是空的，则隐藏结账按钮并显示提示消息
    buyNowButton.style.display = "none";
    const emptyCartMessage = document.createElement("div");
    emptyCartMessage.textContent = "您的購物車目前無商品";
    offcanvasBody.appendChild(emptyCartMessage);
  }
}
// 获取 "buy-now" 元素
const buyNowElement = document.querySelector(".inCart-buyNow");
//loadCartData()END
//----------------------------------------------------------------------
//"在購物車內結帳"
buyNowElement.addEventListener("click", function () {
  // 从本地存储中获取 cartData 数据
  const cartData = JSON.parse(localStorage.getItem("cartData"));

  // 检查 cartData 是否存在
  if (cartData) {
    // 初始化总价为 0
    let totalCost = 0;

    // 遍历 cartData 数组并计算总价
    cartData.forEach((item) => {
      const price = parseFloat(item.Price);
      const quantity = parseInt(item.quantity, 10);
      totalCost += price * quantity;
    });

    // 将总价保存到 localStorage 中
    localStorage.setItem("totalCost", totalCost);

    // 跳转到 Pay.html 页面
    window.location.href = "Pay.html";
  } else {
    // 如果 cartData 不存在，弹出相应信息
    alert("CartData is empty.");
  }
});
//----------------------------------------------------------------------
//按購物車icon執行loadCartData()
// 選擇購物車圖標元素
const cartIcon = document.querySelector(".bi-cart");
// 為購物車圖標添加點擊事件監聽器
// 為購物車圖標添加點擊事件監聽器
cartIcon.addEventListener("click", function () {
  // 获取 offcanvas-body 元素
  const offcanvasBody = document.getElementById("offcanvas-body");

  // 清空 offcanvas-body 内容
  offcanvasBody.innerHTML = "";

  // 当点击购物车图标时，调用 loadCartData() 函数
  loadCartData();

  // 检查 offcanvas-body 的文本内容中是否包含 "總價:"
  const offcanvasText = offcanvasBody.textContent;
  if (!offcanvasText.includes("總價:")) {
    // 如果 offcanvas-body 中没有 "總價:"，则调用 calculateAndAppendTotalPrice() 函数
    calculateAndAppendTotalPrice(offcanvasBody);
  }
});
