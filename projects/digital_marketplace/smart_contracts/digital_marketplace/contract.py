from algopy import (
    Asset,
    Global,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
)

class DigitalMarketplace(arc4.ARC4Contract):
    # The unique identifier for the asset being sold
    assetId: UInt64

    # The price for one unit of the asset
    unitaryPrice: UInt64

    # Create the application with the given asset ID and unitary price
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def createApplication(self, assetId: Asset, unitaryPrice: UInt64) -> None:
        # Set the asset ID and unitary price for the application
        self.assetId = assetId.id
        self.unitaryPrice = unitaryPrice

    # Update the listing price for the asset
    @arc4.abimethod
    def setPrice(self, unitaryPrice: UInt64) -> None:
        # Ensure that only the creator of the application can update the price
        assert Txn.sender == Global.creator_address, "Only the creator can update the price"

        # Update the unitary price for the asset
        self.unitaryPrice = unitaryPrice

    # Opt in to the asset that will be sold
    @arc4.abimethod
    def optInToAsset(self, mbrPay: gtxn.PaymentTransaction) -> None:
        # Ensure that only the creator of the application can opt in to the asset
        assert Txn.sender == Global.creator_address

        # Ensure that the application has not already opted in to the asset
        assert not Global.current_application_address.is_opted_in(Asset(self.assetId))

        # Ensure that the payment receiver is the current application address
        assert mbrPay.receiver == Global.current_application_address

        # Ensure that the payment amount is equal to the minimum balance plus the asset opt-in minimum balance
        assert mbrPay.amount == Global.min_balance + Global.asset_opt_in_min_balance

        # Transfer the asset to the current application address
        itxn.AssetTransfer(
            xfer_asset=self.assetId,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

    # Buy the asset
    @arc4.abimethod
    def buy(self, buyerTxn: gtxn.PaymentTransaction, quantity: UInt64) -> None:
        # Ensure that the unitary price for the asset is not zero
        assert self.unitaryPrice != UInt64(0)

        # Ensure that the sender of the transaction is the same as the buyer
        assert Txn.sender == buyerTxn.sender

        # Ensure that the receiver of the payment is the current application address
        assert buyerTxn.receiver == Global.current_application_address

        # Ensure that the payment amount is equal to the unitary price times the quantity
        assert buyerTxn.amount == self.unitaryPrice * quantity

        # Transfer the asset from the current application address to the buyer
        itxn.AssetTransfer(
            xfer_asset=self.assetId,
            asset_receiver=Txn.sender,
            asset_amount=quantity,
        ).submit()

    # Delete the application
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def deleteApplication(self) -> None:
        # Ensure that only the creator of the application can delete it
        assert Txn.sender == Global.creator_address, "Only the creator can delete the application"

        # Transfer the asset from the current application address back to the creator
        itxn.AssetTransfer(
            xfer_asset=self.assetId,
            asset_receiver=Global.creator_address,
            asset_amount=0,
            asset_close_to=Global.creator_address,
        ).submit()

        # Transfer any remaining balance from the current application address back to the creator
        itxn.Payment(
            receiver=Global.creator_address,
            amount=0,
            close_remainder_to=Global.creator_address,
        ).submit()
